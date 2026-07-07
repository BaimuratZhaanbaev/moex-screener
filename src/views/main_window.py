from datetime import datetime

from loguru import logger
from PySide6.QtCore import QModelIndex, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.api.client import MoexAPIError, MoexClient
from src.core.analytics import DataFilterService
from src.core.constants import DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS
from src.core.parser import MoexDataParser
from src.models.table_model import MoexTableModel
from src.views.filter_panel import FilterPanel


class MainWindow(QMainWindow):
    """Главное окно приложения скринера акций MOEX."""

    def __init__(self):
        super().__init__()
        logger.info("Инициализация графических компонентов MainWindow...")

        # Настройка параметров окна
        self.setWindowTitle("MOEX Stock Screener")
        self.resize(1000, 600)

        # Инициализируем нашу умную Модель данных (Model)
        self.table_model = MoexTableModel()

        # Создаем графический виджет таблицы (Представление / View)
        self.table_view = QTableView(self)

        # Включаем встроенную интерактивную сортировку по клику на заголовки колонок!
        self.table_view.setSortingEnabled(True)

        # СВЯЗЫВАЕМ ИХ ВМЕСТЕ (Паттерн Model-View в действии)
        self.table_view.setModel(self.table_model)
        logger.debug("Модель данных успешно подключена к QTableView.")

        self.filter_panel = FilterPanel()

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        layout.addWidget(self.filter_panel)
        layout.addWidget(self.table_view)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("Система отображения данных готова.")
        logger.success("MainWindow успешно отрисовано.")

        # Коммутация сигналов (Связываем View и Контроллер)

        self.filter_panel.apply_filters_requested.connect(self.handle_filter_changed)
        self.filter_panel.refresh_api_requested.connect(self.handle_refresh_data)
        self.filter_panel.mode_changed.connect(self.handle_mode_changed)
        self.filter_panel.export_requested.connect(self.handle_export_data)

        # Инициализация боевых служб
        self.moex_parser = MoexDataParser()
        self.moex_client = MoexClient()

        # ЗАПУСК: Загружаем реальные данные с биржи!
        self.load_market_data()

    def load_market_data(self):
        """
        Боевой конвейер: скачивает реальные данные через MoexClient,
        обрабатывает их с помощью MoexDataParser и заливает в MoexTableModel.
        """
        logger.info("Запуск штатного обновления данных с Московской Биржи...")
        self.statusBar().showMessage("Запрос данных от MOEX ISS API...")

        try:
            raw_data = self.moex_client.get_clean_data()

            # Передаем сырой JSON в парсер
            df = self.moex_parser.parse_to_dataframe(raw_data)

            if df.empty:
                self.statusBar().showMessage(
                    "Предупреждение: получен пустой массив данных."
                )
                logger.warning("Парсер вернул пустой DataFrame после обработки.")
                return

            self.table_model._source_df = df.copy()

            # Передаем DataFrame в модель Qt
            self.table_model.set_dataframe(df)
            self.handle_mode_changed("basic")

            self.statusBar().showMessage(
                f"Данные успешно обновлены. Всего бумаг в кэше: {len(df)}"
            )
            logger.success("Реальные рыночные данные успешно выведены на экран.")

        except MoexAPIError as e:
            # Обработка сетевых аномалий: изолируем сбой, логируем и оповещаем юзера
            error_msg = f"Ошибка сети MOEX: {str(e)}"
            self.statusBar().showMessage("Не удалось обновить данные.")
            logger.error(error_msg)
            QMessageBox.warning(
                self,
                "Сбой соединения",
                f"Не удалось получить актуальные котировки от биржи.\nПричина: {e}",
            )
        except Exception as e:
            # Защита от непредвиденных критических ошибок
            logger.error(
                f"Непредвиденная ошибка при обновлении интерфейса: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Внутренний сбой системы:\n{e}"
            )

    @Slot(dict)
    def handle_filter_changed(self, filter_params: dict):
        """Слот-Контроллер:

        срабатывает при нажатии кнопки 'Применить' или 'Сбросить'.
        """
        if (
            not hasattr(self.table_model, "_source_df")
            or self.table_model._source_df is None
        ):
            logger.warning(
                "Попытка отфильтровать пустую или неинициализированную модель данных."
            )
            return

        logger.info(f"Запрос на фильтрацию таблицы. Параметры: {filter_params}")

        # Передаем задачу фильтрации в изолированный слой Бизнес-логики
        filtered_df = DataFilterService.filter_market_data(
            df=self.table_model._source_df,
            ticker=filter_params.get("SECID"),
            price_from=filter_params.get("price_from"),
            price_to=filter_params.get("price_to"),
            change_from=filter_params.get("change_from"),
            change_to=filter_params.get("change_to"),
            name=filter_params.get("SHORTNAME"),
        )

        old_df = self.table_model._df
        logger.debug(
            f"Структура: было строк: "
            f"{len(old_df)}, после фильтрации: {len(filtered_df)}"
        )

        # Умное обновление структуры Qt без жесткого Reset при совпадении индексов
        old_len = len(old_df)
        new_len = len(filtered_df)

        # Сценарий 1: Состав и порядок строк не изменились, поменялись только значения
        if list(old_df.index) == list(filtered_df.index):
            self.table_model._df = filtered_df
            if new_len > 0 and len(filtered_df.columns) > 0:
                top_left = self.table_model.index(0, 0)
                bottom_right = self.table_model.index(
                    new_len - 1, len(filtered_df.columns) - 1
                )
                self.table_model.dataChanged.emit(top_left, bottom_right)

        # Сценарий 2: Строки просто удалились с конца (частый случай при фильтрации)
        elif old_df.index.isin(filtered_df.index).all() and new_len < old_len:
            logger.trace("Применение стратегии Qt: точечное удаление строк")

            # Предполагаем, что фильтр отсек хвост.
            # Если структура сложнее, безопаснее использовать reset
            # diff = old_len - new_len
            self.table_model.beginRemoveRows(QModelIndex(), new_len, old_len - 1)
            self.table_model._df = filtered_df
            self.table_model.endRemoveRows()

        # Сценарий 3: Структура изменилась кардинально
        else:
            logger.trace(
                "Применение стратегии Qt: "
                "beginResetModel (критическое изменение структуры)"
            )
            self.table_model.beginResetModel()
            self.table_model._df = filtered_df
            self.table_model.endResetModel()

        # Восстановление интерактивной сортировки пользователя
        header = self.table_view.horizontalHeader()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()

        if sort_column != -1 and len(filtered_df) > 0:
            logger.debug(
                f"Восстановление сортировки. Колонка: "
                f"{sort_column}, Направление: {sort_order}"
            )
            self.table_model.sort(sort_column, sort_order)

        self.statusBar().showMessage(f"Отфильтровано бумаг: {len(filtered_df)}")

    @Slot()
    def handle_refresh_data(self):
        """Мягкая блокировка графического интерфейса при сетевом обмене."""
        logger.info("Пользователь запросил принудительное обновление сети через UI.")

        # 1. Активируем Loading State на кнопке панели
        self.filter_panel.refresh_btn.setEnabled(False)
        self.filter_panel.refresh_btn.setText("⏳ Загрузка...")
        self.statusBar().showMessage(
            "Сетевой обмен: загрузка актуальных котировок MOEX ISS..."
        )

        try:
            # Запускаем штатный метод загрузки
            self.load_market_data()

            # 2. Возвращаем исходное состояние и выводим метку времени
            current_time = datetime.now().strftime("%H:%M:%S")
            self.filter_panel.refresh_btn.setEnabled(True)
            self.filter_panel.refresh_btn.setText("🔄 Обновить данные")
            self.statusBar().showMessage(f"Данные обновлены в {current_time}")

        except Exception:
            # Защита: при любом сбое возвращаем управление кнопкой пользователю
            self.filter_panel.refresh_btn.setEnabled(True)
            self.filter_panel.refresh_btn.setText("🔄 Обновить данные")
            self.statusBar().showMessage("Ошибка при обновлении данных.")
            logger.exception("Критический сбой мягкой блокировки при сетевом запросе")

    @Slot(str)
    def handle_mode_changed(self, mode: str):
        """Динамическое скрытие колонок в QTableView на основе выбранного режима."""
        try:
            logger.info(f"Переключение пресета колонок таблицы на режим: '{mode}'")

            if not self.table_model or self.table_model._df is None:
                logger.warning(
                    "Отмена переключения режима: "
                    "модель или данные еще не инициализированы."
                )
                return

            # Определяем список разрешенных колонок для каждого режима
            if mode == "basic":
                allowed_columns = DEFAULT_COLUMNS
            elif mode == "professional":
                allowed_columns = PROFESSIONAL_COLUMNS
            else:  # Режим "full" (Все поля)
                allowed_columns = (
                    list(self.table_model._source_df.columns)
                    if self.table_model._source_df is not None
                    else []
                )

            # Запускаем цикл скрытия/отображения по всем столбцам QTableView
            for i in range(self.table_model.columnCount()):
                # Безопасно вытаскиваем техническое имя колонки из DataFrame по индексу
                if i < len(self.table_model._df.columns):
                    col_name = self.table_model._df.columns[i]
                else:
                    continue

                # Скрываем колонку, если её имени нет в списке разрешенных
                is_hidden = col_name not in allowed_columns
                self.table_view.setColumnHidden(i, is_hidden)

            self.statusBar().showMessage(f"Применен режим отображения: {mode}")
            logger.success(f"Сетка колонок успешно перестроена для режима '{mode}'.")

        except Exception as e:
            logger.exception(
                f"Ошибка динамической перестройки колонок для режима {mode}"
            )
            QMessageBox.critical(
                self, "Ошибка интерфейса", f"Не удалось изменить режим отображения: {e}"
            )

    @Slot(str)
    def handle_export_data(self, file_format: str):
        """Безопасный экспорт отфильтрованного среза данных в CSV."""
        if file_format != "csv":
            return

        # 1. Валидация: Не даем выгрузить пустую таблицу
        if self.table_model.rowCount() == 0:
            logger.warning("Блокировка экспорта: таблица не содержит записей.")
            QMessageBox.warning(
                self,
                "Экспорт",
                "Невозможно экспортировать пустую таблицу. Смягчите фильтры!",
            )
            return

        try:
            # 2. Открываем системный диалог выбора пути сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить экспорт биржевых данных",
                "",
                "Comma Separated Values (*.csv);;All Files (*)",
            )

            if not file_path:
                logger.info("Экспорт отменен пользователем.")
                return

            # 3. Извлекаем текущий отфильтрованный срез DataFrame из модели
            export_df = self.table_model._df

            # 4. Безопасная запись на диск
            export_df.to_csv(file_path, index=False, encoding="utf-8-sig")

            logger.info(f"Данные успешно экспортированы в: {file_path}")
            self.statusBar().showMessage(f"Файл успешно сохранен: {file_path}")
            QMessageBox.information(self, "Экспорт", "Данные успешно сохранены в файл!")

        except Exception as e:
            logger.exception("Критическая ошибка при записи CSV файла на жесткий диск")
            QMessageBox.critical(
                self, "Ошибка экспорта", f"Не удалось сохранить файл:\n{e}"
            )

    def closeEvent(self, event: QCloseEvent):
        """Вызывается автоматически при закрытии главного окна пользователем"""

        logger.info("Пользователь инициировал закрытие главного окна.")

        # Здесь в будущем можно добавить логику:
        # Например: self.save_user_settings() или self.http_client.close()

        # Разрешаем окну закрыться
        event.accept()
