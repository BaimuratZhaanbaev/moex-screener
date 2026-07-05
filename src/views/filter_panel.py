# src/views/filter_panel.py
from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class FilterPanel(QWidget):
    """
    Графическая панель управления пресетами отображения,
    экспортом и фильтрацией биржевых данных.
    """

    # Объявляем сигналы для взаимодействия с MainWindow
    mode_changed = Signal(str)  # Передает: "basic", "professional", "full"
    export_requested = Signal(str)  # Передает: "csv"
    refresh_api_requested = Signal()  # Сигнал на обновление данных из сети
    apply_filters_requested = Signal(dict)  # Передает словарь с активными фильтрами

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Корневой слой панели
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 10)  # Отступ снизу до таблицы

        # Создаем визуальный контейнер QFrame для всей панели
        main_frame = QFrame()
        main_frame.setObjectName("FilterPanelFrame")
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(8)

        # Загрузка стилей из внешнего QSS файла
        qss_path = "src/resources/styles.qss"
        try:
            with open(qss_path, encoding="utf-8") as f:
                self.setStyleSheet(f.read())
            logger.info(f"Стили интерфейса успешно загружены из {qss_path}")
        except FileNotFoundError as e:
            logger.exception(
                f"Критическая ошибка: Файл стилей не найден по пути {qss_path}"
            )
            raise FileNotFoundError(
                f"Не удалось запустить FilterPanel: отсутствует файл стилей {qss_path}"
            ) from e
        
        # ------------------------------------------------------------------------------
        # Уровень 1: Управляющий слой (Верхний ряд)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # Селектор режимов отображения колонок
        mode_label = QLabel("Режим отображения:")
        self.mode_combo = QComboBox()
        # userData используется для хранения технического имени режима
        self.mode_combo.addItem("Базовый", userData="basic")
        self.mode_combo.addItem("Профессиональный", userData="professional")
        self.mode_combo.addItem("Сырой JSON (Все поля)", userData="full")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        # Модуль экспорта в файлы
        export_label = QLabel("Экспорт:")
        self.export_combo = QComboBox()
        self.export_combo.addItem("Экспорт в...")
        self.export_combo.addItem("CSV (.csv)", userData="csv")
        self.export_combo.currentIndexChanged.connect(self._on_export_changed)

        # Горизонтальная выравнивающая распорка (Spacer)
        spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Кнопка асинхронного обновления API ISS
        self.refresh_btn = QPushButton("🔄 Обновить данные")
        self.refresh_btn.setObjectName("RefreshBtn")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)

        # Сборка верхней строки
        top_layout.addWidget(mode_label)
        top_layout.addWidget(self.mode_combo)
        top_layout.addWidget(export_label)
        top_layout.addWidget(self.export_combo)
        top_layout.addSpacerItem(spacer)
        top_layout.addWidget(self.refresh_btn)

        # ------------------------------------------------------------------------------
        # Уровень 2: Аналитические фильтры (Нижний ряд)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        # Текстовый поиск (SECID и SHORTNAME)
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Тикер...")
        self.ticker_input.setFixedWidth(90)
        self.ticker_input.textChanged.connect(
            lambda: self._update_widget_style(self.ticker_input)
            )

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Наименование...")
        self.name_input.setFixedWidth(140)
        self.name_input.textChanged.connect(
            lambda: self._update_widget_style(self.name_input)
            )
        
        # Фильтры цен (LAST) с точностью 4 знака
        price_label = QLabel("Цена от:")
        self.price_from = QDoubleSpinBox()
        self.price_from.setDecimals(4)
        self.price_from.setMaximum(1000000.0)
        self.price_from.setSpecialValueText("—")
        self.price_from.valueChanged.connect(
            lambda: self._update_widget_style(self.price_from)
            )

        price_to_label = QLabel("до:")
        self.price_to = QDoubleSpinBox()
        self.price_to.setDecimals(4)
        self.price_to.setMaximum(1000000.0)
        self.price_to.setSpecialValueText("—")
        self.price_to.valueChanged.connect(
            lambda: self._update_widget_style(self.price_to)
            )

        # ------------------------------------------------------------------------------

        # Добавляем обе строки в разметку фрейма
        frame_layout.addLayout(top_layout)
        frame_layout.addLayout(bottom_layout)

        # Помещаем фрейм в корневой слой виджета
        root_layout.addWidget(main_frame)

    # Внутренние слоты для перенаправления сигналов с техническими параметрами
    def _on_mode_changed(self, index):
        try:
            technical_mode = self.mode_combo.itemData(index)

            if technical_mode:
                logger.debug(
                    f"Смена режима отображения на: '{technical_mode}' (индекс: {index})"
                )

                self.mode_changed.emit(technical_mode)
            else:
                logger.warning(f"Получен пустой режим userData для индекса {index}")
        except Exception as e:
            logger.exception(
                f"Ошибка при обработке изменения режима отображения (индекс: {index})"
            )
            raise RuntimeError(
                "Сбой графического интерфейса при смене режима фильтрации"
            ) from e

    def _on_export_changed(self, index):
        try:
            technical_format = self.export_combo.itemData(index)

            if technical_format == "csv":
                logger.info("Запрошен экспорт данных в формат CSV")

                self.export_requested.emit("csv")

                # Временно блокируем сигналы, чтобы сброс индекса не вызвал метод заново
                self.export_combo.blockSignals(True)
                self.export_combo.setCurrentIndex(0)
                self.export_combo.blockSignals(False)  # Возвращаем отслеживание обратно
        except Exception as e:
            logger.exception(
                f"Ошибка при обработке запроса на экспорт (индекс: {index})"
            )
            raise RuntimeError(
                "Сбой графического интерфейса при экспорте данных"
            ) from e

    def _on_refresh_clicked(self):
        try:
            logger.info("Пользователь нажал кнопку обновления API данных")

            self.refresh_api_requested.emit()
        except Exception as e:
            logger.exception("Ошибка при генерации сигнала обновления данных API")
            raise RuntimeError(
                "Сбой графического интерфейса при попытке обновить данные"
            ) from e
