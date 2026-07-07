# src/views/filter_panel.py
from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
        bottom_layout.setSpacing(12)

        # Текстовый поиск (SECID и SHORTNAME)
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Тикер...")
        self.ticker_input.setMinimumWidth(80)
        self.ticker_input.setMaximumWidth(100)
        self.ticker_input.textChanged.connect(
            lambda: self._update_widget_style(self.ticker_input)
        )

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Наименование...")
        self.name_input.setMinimumWidth(120)
        self.name_input.setMaximumWidth(160)
        self.name_input.textChanged.connect(
            lambda: self._update_widget_style(self.name_input)
        )

        # Фильтры цен (LAST) с точностью 4 знака
        price_label = QLabel("Цена от:")
        self.price_from = QDoubleSpinBox()
        self.price_from.setDecimals(4)
        self.price_from.setMinimum(0.0)
        self.price_from.setMaximum(1000000.0)
        self.price_from.setValue(0.0)
        self.price_from.setMinimumWidth(100)
        self.price_from.setSpecialValueText("—")
        self.price_from.valueChanged.connect(
            lambda: self._update_widget_style(self.price_from)
        )

        price_to_label = QLabel("до:")
        self.price_to = QDoubleSpinBox()
        self.price_to.setDecimals(4)
        self.price_to.setMinimum(0.0)
        self.price_to.setMaximum(1000000.0)
        self.price_to.setValue(0.0)
        self.price_to.setMinimumWidth(100)
        self.price_to.setSpecialValueText("—")
        self.price_to.valueChanged.connect(
            lambda: self._update_widget_style(self.price_to)
        )

        # Фильтры изменений (LASTTOPREVPRICE) с диапазоном отрицательных чисел
        change_label = QLabel("Изм. % от:")
        self.change_from = QDoubleSpinBox()
        self.change_from.setDecimals(2)
        self.change_from.setMinimum(-100.0)
        self.change_from.setMaximum(100.0)
        self.change_from.setValue(-100.0)
        self.change_from.setSpecialValueText("—")
        self.change_from.valueChanged.connect(
            lambda: self._update_widget_style(self.change_from)
        )

        change_to_label = QLabel("до:")
        self.change_to = QDoubleSpinBox()
        self.change_to.setDecimals(2)
        self.change_to.setMinimum(-100.0)
        self.change_to.setMaximum(100.0)
        self.change_to.setValue(-100.0)
        self.change_to.setSpecialValueText("—")
        self.change_to.valueChanged.connect(
            lambda: self._update_widget_style(self.change_to)
        )

        # Вертикальный микро-разделитель между фильтрами и кнопками действий
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)

        # Кнопки действий
        self.apply_btn = QPushButton("🚀 Применить")
        self.apply_btn.setObjectName("ApplyBtn")
        self.apply_btn.clicked.connect(self._on_apply_clicked)

        self.reset_btn = QPushButton("❌ Сбросить")
        self.reset_btn.setObjectName("ResetBtn")
        self.reset_btn.clicked.connect(self._on_reset_clicked)

        # Сборка нижней строки аналитических фильтров
        bottom_layout.addWidget(self.ticker_input)
        bottom_layout.addWidget(self.name_input)
        bottom_layout.addWidget(price_label)
        bottom_layout.addWidget(self.price_from)
        bottom_layout.addWidget(price_to_label)
        bottom_layout.addWidget(self.price_to)
        bottom_layout.addWidget(change_label)
        bottom_layout.addWidget(self.change_from)
        bottom_layout.addWidget(change_to_label)
        bottom_layout.addWidget(self.change_to)
        bottom_layout.addWidget(divider)
        bottom_layout.addWidget(self.apply_btn)
        bottom_layout.addWidget(self.reset_btn)

        # ------------------------------------------------------------------------------

        # Добавляем обе строки в разметку фрейма
        frame_layout.addLayout(top_layout)
        frame_layout.addLayout(bottom_layout)

        # Помещаем фрейм в корневой слой виджета
        root_layout.addWidget(main_frame)

    # ----------------------------------------------------------------------------------
    # Логический слой и UI/UX механики

    def _is_widget_active(self, widget: QWidget) -> bool:
        """Вспомогательный метод для точного определения активности фильтра."""
        if isinstance(widget, QLineEdit):
            return len(widget.text().strip()) > 0
            
        if isinstance(widget, QDoubleSpinBox):
            return widget.value() > widget.minimum()
        
        return False

    def _update_widget_style(self, widget: QWidget):
        """Динамическая подсветка активных полей ввода на основе флага активности."""
        is_active = False
        if isinstance(widget, QLineEdit):
            is_active = bool(widget.text().strip())
        elif isinstance(widget, QDoubleSpinBox):
            is_active = self._is_widget_active(widget)

        widget.setProperty("active", is_active)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def get_filter_params(self) -> dict:
        """
        Конвейер сборки параметров: считывает данные из виджетов
        и упаковывает в очищенный словарь для слоя Pandas.
        """
        ticker = self.ticker_input.text().strip().upper()
        name = self.name_input.text().strip()

        # Если числовое поле показывает "—", возвращаем None
        p_from = (
            self.price_from.value() 
            if self._is_widget_active(self.price_from) 
            else None
            )
        p_to = (
            self.price_to.value() 
            if self._is_widget_active(self.price_to) 
            else None
            )
        c_from = (
            self.change_from.value() 
            if self._is_widget_active(self.change_from) 
            else None
            )
        c_to = (
            self.change_to.value() 
            if self._is_widget_active(self.change_to) 
            else None
            )

        return {
            "SECID": ticker if ticker else None,
            "SHORTNAME": name if name else None,
            "price_from": p_from,
            "price_to": p_to,
            "change_from": c_from,
            "change_to": c_to,
        }

    def _on_apply_clicked(self):
        """Слот обработки клика по кнопке 'Применить'."""
        try:
            params = self.get_filter_params()
            logger.info(f"Пользователь применил фильтры бизнес-логики: {params}")
            self.apply_filters_requested.emit(params)
        except Exception as e:
            logger.exception(
                "Критическая ошибка при формировании параметров фильтрации"
            )
            raise RuntimeError(
                "Сбой графического интерфейса при фильтрации данных"
            ) from e

    def _on_reset_clicked(self):
        """Слот интеллектуального сброса всех фильтров в дефолтное состояние."""
        try:
            logger.info("Пользователь инициировал полный сброс панели фильтров")

            # Очищаем текстовые поля
            self.ticker_input.clear()
            self.name_input.clear()

            # Сбрасываем числовые счетчики на минимум (чтобы отобразился прочерк "—")
            self.price_from.setValue(self.price_from.minimum())
            self.price_to.setValue(self.price_to.minimum())
            self.change_from.setValue(self.change_from.minimum())
            self.change_to.setValue(self.change_to.minimum())

            # Возвращаем режим отображения колонок в "Базовый"
            self.mode_combo.setCurrentIndex(0)

            # Эмитим сигнал применения пустых фильтров, чтобы вернуть исходную таблицу
            self.apply_filters_requested.emit(self.get_filter_params())
        except Exception as e:
            logger.exception("Ошибка при выполнении сброса параметров интерфейса")
            raise RuntimeError("Сбой графической подсистемы при сбросе настроек") from e

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
