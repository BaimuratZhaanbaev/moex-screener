"""Главный контроллер графического интерфейса скринера акций MOEX.

Управляет жизненным циклом оконных компонентов, связывает сетевой слой ISS API
с кастомной моделью данных и координирует реакцию UI на действия пользователя.
"""

import os
from datetime import datetime
from typing import Any

from loguru import logger
from PySide6.QtCore import QModelIndex, Slot, Qt
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
from src.core.config import UIConfig
from src.core.parser import MoexDataParser
from src.models.table_model import MoexTableModel
from src.views.filter_panel import FilterCriteria, FilterPanel
from src.core.constants import DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS


class MainWindow(QMainWindow):
    """Главное окно приложения скринера акций MOEX."""

    def __init__(self):
        """Инициализирует графическое окружение, подсистемы конфигурации и модель."""
        super().__init__()
        logger.info("Инициализация графических компонентов MainWindow...")

        # Настройка параметров окна
        self.setWindowTitle("MOEX Stock Screener")
        self.resize(1000, 600)

        # Инициализация инфраструктурных слоев
        self.ui_config = UIConfig()
        self.table_model = MoexTableModel()
        self.api_client = MoexClient()

        # Создаем графический виджет таблицы (Представление / View)
        self.table_view = QTableView(self)

        # Включаем встроенную интерактивную сортировку по клику на заголовки колонок!
        self.table_view.setSortingEnabled(True)

        # СВЯЗЫВАЕМ ИХ ВМЕСТЕ (Паттерн Model-View в действии)
        self.table_view.setModel(self.table_model)
        logger.debug("Модель данных успешно подключена к QTableView.")

        # Активируем чередование цветов строк
        self.table_view.setAlternatingRowColors(True)

        self.filter_panel = FilterPanel()

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.filter_panel)
        layout.addWidget(self.table_view)
        self.setCentralWidget(central_widget)

        self.statusBar().showMessage("Система отображения данных готова.")
        logger.success("MainWindow успешно отрисовано.")

        # Коммутация сигналов (Связываем View и Контроллер)

        self.filter_panel.apply_filters_requested.connect(self._on_apply_filters)
        self.filter_panel.refresh_api_requested.connect(self._on_refresh_data)
        self.filter_panel.mode_changed.connect(self._on_display_mode_changed)
        self.filter_panel.export_requested.connect(self._on_export_requested)

        # Инициализация боевых служб
        self.moex_parser = MoexDataParser()
        self.moex_client = MoexClient()

        # Скачиваем данные с биржи и выводим на экран
        self._on_refresh_data()

    @Slot()
    def _on_refresh_data(self) -> None:
        """Выполняет штатное обновление рыночных данных с Московской Биржи.

        Активирует состояние загрузки в интерфейсе, запрашивает сырые данные через
        API клиент, парсит их в DataFrame и обновляет табличную модель. В случае
        успеха актуализирует видимость колонок и выводит статусную информацию.
        """
        logger.info("Запуск штатного обновления данных с Московской Биржи...")
        # 1. Активируем Loading State на кнопке панели
        self.filter_panel.btn_refresh.setEnabled(False)
        self.filter_panel.btn_refresh.setText("⏳ Загрузка...")
        self.statusBar().showMessage("Запрос данных от MOEX ISS API...")

        try:
            # Сетевой запрос к ISS API
            raw_data = self.moex_client.get_clean_data()

            # Передаем сырой JSON в парсер
            full_df = self.moex_parser.parse_to_dataframe(raw_data)

            if full_df.empty:
                self.statusBar().showMessage("Ошибка: получен пустой массив данных.")
                logger.warning("Парсер вернул пустой DataFrame после обработки.")

                # Защита: возвращаем исходное состояние кнопке
                self.filter_panel.btn_refresh.setEnabled(True)
                self.filter_panel.btn_refresh.setText("🔄 Обновить данные")
                return

            self.table_model._source_df = full_df.copy()

            # Передаем DataFrame в модель Qt
            self.table_model.set_dataframe(full_df)
            
            # Актуализируем видимость столбцов согласно текущему UIConfig
            self._update_column_visibility()

            timestamp = datetime.now().strftime("%H:%M:%S")
            self.filter_panel.btn_refresh.setEnabled(True)
            self.filter_panel.btn_refresh.setText("🔄 Обновить данные")
            self.statusBar().showMessage(
                f"Данные успешно обновлены в {timestamp}. Всего бумаг: {len(full_df)}"
            )

            logger.success("Реальные рыночные данные успешно выведены на экран.")

        except MoexAPIError as e:
            # Возвращаем кнопку при сетевой ошибке
            self.filter_panel.btn_refresh.setEnabled(True)
            self.filter_panel.btn_refresh.setText("🔄 Обновить данные")
        
            # Обработка сетевых аномалий: изолируем сбой, логируем и оповещаем юзера
            self.statusBar().showMessage("Ошибка соединения с сервером MOEX.")
            logger.error("Ошибка сети MOEX: {}", str(e))
            QMessageBox.warning(
                self,
                "Сбой соединения",
                f"Не удалось получить актуальные котировки от биржи.\nПричина: {e}",
            )
        except Exception as e:
            # Возвращаем кнопку при любом непредвиденном сбое
            self.filter_panel.btn_refresh.setEnabled(True)
            self.filter_panel.btn_refresh.setText("🔄 Обновить данные")

            # Защита от непредвиденных критических ошибок
            logger.error(
                f"Непредвиденная ошибка при обновлении интерфейса: {e}", exc_info=True
            )
            QMessageBox.critical(
                self, "Критическая ошибка", f"Внутренний сбой системы:\n{e}"
            )

    @Slot(FilterCriteria)
    def _on_apply_filters(self, criteria: FilterCriteria) -> None:
        """Применяет критерии фильтрации к табличной модели данных.

        Анализирует входящие критерии. Если запрос пустой, сбрасывает системную
        сортировку таблицы. Передает фильтрацию в бизнес-логику и применяет
        результаты к модели с использованием оптимальной Qt-стратегии обновления
        строк. В конце восстанавливает пользовательскую сортировку.

        Args:
            criteria: Объект dataclass или модели с параметрами фильтрации.
        """
        logger.info("Контроллер принял команду фильтрации: {}", criteria)

        # Проверка на полный сброс панели фильтров
        is_reset = all(
            value is None
            for value in (
                criteria.ticker,
                criteria.name,
                criteria.price_from,
                criteria.price_to,
                criteria.change_from,
                criteria.change_to,
            )
        )

        if is_reset:
            logger.info("Обнаружен запрос на сброс. Сбрасываем сортировку таблицы...")
            
            # Отключаем сортировку в самом View
            self.table_view.setSortingEnabled(False)
            
            # Сбрасываем визуальный индикатор (стрелочку) на заголовке таблицы
            header = self.table_view.horizontalHeader()
            header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            
            if hasattr(self.table_model, "sort"):
                self.table_model.sort(-1) 
            
            # Включаем возможность сортировки обратно для пользователя
            self.table_view.setSortingEnabled(True)

        # Получаем эталонный мастер-массив
        master_df = self.table_model._source_df

        if master_df.empty:
            self.statusBar().showMessage("Фильтрация невозможна: кэш данных пуст.")
            return

        # Передаем задачу фильтрации в изолированный слой Бизнес-логики
        filtered_df = DataFilterService.filter_market_data(
            df=master_df,
            ticker=criteria.ticker or "",
            name=criteria.name or "",
            price_from=criteria.price_from,
            price_to=criteria.price_to,
            change_from=criteria.change_from,
            change_to=criteria.change_to,
        )

        old_df = self.table_model._df
        logger.debug(
            "Структура: было строк: {}, после фильтрации: {}",
            len(old_df),
            len(filtered_df),
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
                "Восстановление сортировки. Колонка: {}, Направление: {}",
                sort_column,
                sort_order,
            )
            self.table_model.sort(sort_column, sort_order)

        self.statusBar().showMessage(f"Отфильтровано бумаг: {len(filtered_df)}")


    @Slot(str)
    def _on_display_mode_changed(self, new_mode: str) -> None:
        """Обрабатывает сигнал изменения пресета отображения колонок.

        Сохраняет выбранный режим в конфигурацию интерфейса и инициирует
        динамическую перестройку видимости столбцов таблицы.

        Args:
            new_mode: Строковый идентификатор нового режима (например, 'basic').
        """
        logger.info("Запрос переключения пресета колонок на: {}", new_mode)
        self.ui_config.current_mode = new_mode
        self._update_column_visibility()

    def _update_column_visibility(self) -> None:
        """Динамически изменяет видимость столбцов таблицы под текущий режим.

        Скрывает или отображает секции горизонтального заголовка таблицы на основе
        разрешенных списков колонок (DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS) для
        выбранного пресета. Если данные отсутствуют, выполнение прерывается.
        """
        # Инициализируем переменную для безопасного логирования в блоке except
        mode = getattr(self.ui_config, "current_mode", "unknown")
        try:
            if (
                not self.table_model
                or self.table_model._df is None
                or self.table_model._df.empty
            ):

                logger.warning(
                    "Отмена переключения режима: "
                    "модель или данные еще не инициализированы."
                )
                return
            
            # Получаем текущий активный режим
            mode = self.ui_config.current_mode
            logger.info("Запущена перестройка сетки колонок для режима: '{}'", mode)

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
            
            header = self.table_view.horizontalHeader()
            all_cols = list(self.table_model._df.columns)

            # Запускаем цикл скрытия/отображения по всем столбцам QTableView
            for logical_index in range(self.table_model.columnCount()):
                col_name = all_cols[logical_index]
                
                # Если колонка есть в разрешенном списке — показываем, иначе скрываем
                if col_name in allowed_columns:
                    header.showSection(logical_index)
                else:
                    header.hideSection(logical_index)

            self.statusBar().showMessage(f"Применен режим отображения: {mode}")
            logger.success("Сетка колонок успешно перестроена для режима '{}'.", mode)

        except Exception as e:
            logger.exception(
                "Ошибка динамической перестройки колонок для режима {}", mode
            )
            QMessageBox.critical(
                self, "Ошибка интерфейса", f"Не удалось изменить режим отображения: {e}"
            )

    @Slot(str)
    def _on_export_requested(self, file_format: str) -> None:
        """Безопасно экспортирует отфильтрованный срез данных в CSV-файл.

        Проверяет формат и наличие данных в модели. Вызывает системный диалог
        выбора пути для сохранения файла. При успешном выборе записывает данные
        на диск с кодировкой 'utf-8-sig' для корректного отображения в Excel.

        Args:
            file_format: Строковый идентификатор целевого формата.
                Метод обрабатывает только значение 'csv'.
        """
        if file_format != "csv":
            return

        # Извлекаем текущий отфильтрованный срез DataFrame из модели
        export_df = self.table_model._df

        # Валидация: Не даем выгрузить пустую таблицу
        if export_df.empty:
            logger.warning("Блокировка экспорта: таблица не содержит записей.")
            QMessageBox.warning(
                self,
                "Экспорт",
                "Невозможно экспортировать пустую таблицу. Смягчите фильтры!",
            )
            return

        try:
            # Открываем системный диалог выбора пути сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить экспорт биржевых данных",
                "",
                "Comma Separated Values (*.csv);;All Files (*)",
            )

            if not file_path:
                logger.info("Экспорт отменен пользователем.")
                return

            # Безопасная запись на диск
            export_df.to_csv(file_path, index=False, encoding="utf-8-sig")

            logger.info("Данные успешно экспортированы в: {}", file_path)
            self.statusBar().showMessage("Файл успешно сохранен: {}", file_path)
            QMessageBox.information(self, "Экспорт", "Данные успешно сохранены в файл!")

        except Exception as e:
            logger.exception("Критическая ошибка при записи CSV файла на жесткий диск")
            QMessageBox.critical(
                self, "Ошибка экспорта", f"Не удалось сохранить файл:\n{e}"
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Перехватывает и обрабатывает событие закрытия главного окна приложения.

        Вызывается автоматически средой Qt при попытке пользователя закрыть
        окно. Позволяет выполнить финализацию ресурсов и сохранение настроек
        перед завершением жизненного цикла приложения.

        Args:
            event: Графический объект события закрытия окна от Qt.
        """
        logger.info("Пользователь инициировал закрытие главного окна.")

        # Здесь в будущем можно добавить логику:
        # Например: self.save_user_settings() или self.http_client.close()

        event.accept()
