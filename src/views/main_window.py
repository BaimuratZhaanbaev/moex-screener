from loguru import logger
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.api.client import MoexAPIError, MoexClient
from src.core.analytics import DataFilterService
from src.core.constants import PROFESSIONAL_COLUMNS
from src.core.parser import MoexDataParser
from src.models.table_model import MoexTableModel


class MainWindow(QMainWindow):
    """Главное окно приложения скринера акций MOEX."""

    def __init__(self):
        super().__init__()
        logger.info("Инициализация графических компонентов MainWindow...")

        # Настройка параметров окна
        self.setWindowTitle("MOEX Stock Screener")
        self.resize(1000, 600)

        # Создаем графический виджет таблицы (Представление / View)
        self.table_view = QTableView(self)

        # Включаем встроенную интерактивную сортировку по клику на заголовки колонок!
        self.table_view.setSortingEnabled(True)

        # Инициализируем нашу умную Модель данных (Model)
        self.table_model = MoexTableModel()

        # СВЯЗЫВАЕМ ИХ ВМЕСТЕ (Паттерн Model-View в действии)
        self.table_view.setModel(self.table_model)
        logger.debug("Модель данных успешно подключена к QTableView.")

        # Располагаем таблицу внутри окна
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.table_view)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("Система отображения данных готова.")
        logger.success("MainWindow успешно отрисовано.")

        # 4. ИНИЦИАЛИЗАЦИЯ БОЕВЫХ СЛУЖБ
        # Создаем экземпляр твоего парсера и передаем ему список разрешенных колонок
        self.moex_parser = MoexDataParser(allowed_columns=PROFESSIONAL_COLUMNS)
        self.moex_client = MoexClient()

        # ЗАПУСК: Загружаем реальные данные с биржи вместо фейкового теста!
        self.load_market_data()

    def load_market_data(self):
        """
        Боевой конвейер: скачивает реальные данные через MoexClient,
        обрабатывает их с помощью MoexDataParser и заливает в MoexTableModel.
        """
        logger.info("Запуск штатного обновления данных с Московской Биржи...")
        self.statusBar().showMessage("Запрос данных от MOEX ISS API...")

        try:
            # Временная заглушка
            raw_data = self.moex_client.get_clean_data(
                use_fixture="securities_valid_little.json"
            )

            # Передаем сырой JSON в твой динамический пар
            df = self.moex_parser.parse_to_dataframe(raw_data)

            if df.empty:
                self.statusBar().showMessage(
                    "Предупреждение: получен пустой массив данных."
                )
                logger.warning("Парсер вернул пустой DataFrame после обработки.")
                return

            # Передаем DataFrame в модель Qt
            self.table_model.set_dataframe(df)

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

    def handle_filter_changed(self):
        """Слот-Контроллер: срабатывает при изменении параметров фильтрации."""

        # Забираем сырые данные из полей ввода View
        ticker_query = self.filter_panel.get_ticker()
        price_min = self.filter_panel.get_price_from()
        # ... получение остальных параметров ...

        logger.info(
            f"Запрос на фильтрацию таблицы. Параметры -> "
            f"Тикер: '{ticker_query}', Мин. цена: {price_min}"
        )

        # Передаем задачу в изолированный слой Бизнес-логики
        filtered_df = DataFilterService.filter_market_data(
            df=self.table_model._source_df,
            ticker=ticker_query,
            price_from=price_min,
            # ... остальные параметры ...
        )

        # Умное обновление структуры Qt без жесткого Reset
        old_df = self.table_model._df

        logger.debug(
            f"Анализ структуры данных: было строк: {len(old_df)}, "
            f"после фильтрации: {len(filtered_df)}"
        )

        # Если данные принципиально изменились по составу строк,
        # используем точечные транзакции Qt вместо тотального resetModel
        if list(old_df.index) != list(filtered_df.index):
            # Стратегия для фильтрации: если строк стало меньше, мы их "удаляем" для Qt
            if len(filtered_df) < len(old_df):
                logger.trace(
                    "Применение стратегии Qt: "
                    "beginResetModel (состав строк сильно уменьшился)"
                )

                # Для сильного изменения сброс допустим
                self.table_model.beginResetModel()
                self.table_model._df = filtered_df
                self.table_model.endResetModel()
            else:
                logger.trace(
                    "Применение стратегии Qt: dataChanged для всего диапазона ячеек"
                )

                # Если структура не разрушена, а поменялись только значения цен
                # Мы просто уведомляем Qt, что данные внутри ячеек обновились,
                self.table_model._df = filtered_df
                top_left = self.table_model.index(0, 0)
                bottom_right = self.table_model.index(
                    len(filtered_df) - 1, len(filtered_df.columns) - 1
                )
                self.table_model.dataChanged.emit(top_left, bottom_right)
        else:
            logger.trace(
                "Применение стратегии Qt: "
                "dataChanged «на лету» (изменились только значения цен)"
            )
            # Если состав строк тот же, просто обновились цены в ячейках
            self.table_model._df = filtered_df
            self.table_model.dataChanged.emit(
                self.table_model.index(0, 0),
                self.table_model.index(
                    len(filtered_df) - 1, len(filtered_df.columns) - 1
                ),
            )

        # Принудительно возвращаем строки в тот порядок, который выбрал пользователь
        header = self.table_view.horizontalHeader()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()

        # Вызываем сортировку модели для нового отфильтрованного набора данных
        if sort_column != -1:  # Проверяем, активна ли сортировка вообще
            logger.debug(
                f"Восстановление сортировки после фильтрации. "
                f"Колонка индекс: {sort_column}, Направление: {sort_order}"
            )

            self.table_model.sort(sort_column, sort_order)

        self.statusBar().showMessage(f"Отфильтровано бумаг: {len(filtered_df)}")

    def closeEvent(self, event: QCloseEvent):
        """Вызывается автоматически при закрытии главного окна пользователем"""

        logger.info("Пользователь инициировал закрытие главного окна.")

        # Здесь в будущем можно добавить логику:
        # Например: self.save_user_settings() или self.http_client.close()

        # Разрешаем окну закрыться
        event.accept()
