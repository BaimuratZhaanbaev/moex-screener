"""Графические компоненты панели управления и фильтрации данных (View).

Модуль инкапсулирует элементы интерактивного пользовательского интерфейса
для тонкой настройки выборок, переключения пресетов и триггеров экспорта.
"""



from dataclasses import dataclass

from typing import Final
from loguru import logger
from PySide6.QtCore import Signal, Slot
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

from src.core.constants import ViewMode, ExportFormat


@dataclass(frozen=True)
class FilterCriteria:
    """Неизменяемый объект переноса данных (DTO) критериев фильтрации рыночных данных.

    Используется для безопасной передачи параметров поиска между слоем
    графического интерфейса (View) и бизнес-логикой (Controller/Presenter/Model).
    Все строковые поля нормализуются (удаляются пробелы, приводится к верхнему регистру).

    Attributes:
        ticker (str | None): Уникальный краткий идентификатор ценной бумаги 
            (например, "SBER", "GAZP"). None, если фильтр по тикеру отключен.
        name (str | None): Часть полного или краткого наименования компании для 
            контекстного поиска. None, если поиск по имени отключен.
        price_from (float | None): Нижняя граница стоимости ценной бумаги. 
            None означает отсутствие ограничения снизу.
        price_to (float | None): Верхняя граница стоимости ценной бумаги. 
            None означает отсутствие ограничения сверху.
        change_from (float | None): Минимально допустимое изменение цены акций в процентах. 
            Может быть отрицательным. None означает отсутствие лимита.
        change_to (float | None): Максимально допустимое изменение цены акций в процентах. 
            None означает отсутствие лимита.
    """

    ticker: str | None
    name: str | None
    price_from: float | None
    price_to: float | None
    change_from: float | None
    change_to: float | None


class NullableDoubleSpinBox(QDoubleSpinBox):
    """Кастомный числовой спинбокс с поддержкой пустого состояния (Null/None).

    Расширяет стандартный `QDoubleSpinBox`, позволяя визуально скрывать числовое
    значение, отображая абсолютно пустую строку, если данные не были введены.
    Решает проблему разделения понятий «пользователь ввел ноль (0.0)» и 
    «пользователь оставил поле пустым (None)».

    В отличие от базового класса, динамически проверяет состояние текстового 
    интерфейса, не сохраняя дублирующие флаги активности во внутренней памяти.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализирует NullableDoubleSpinBox и устанавливает начальное пустое состояние.

        Args:
            parent (QWidget | None): Родительский виджет. По умолчанию None.
        """
        super().__init__(parent)
        self.setMinimumWidth(90)

        # По умолчанию принудительно очищаем строку ввода при старте
        self.clear()

    def clear(self) -> None:
        """Сбрасывает поле в пустое состояние.

        Очищает текст, устанавливает внутреннее значение по умолчанию (0.0)
        и принудительно перерисовывает виджет.
        """
        super().clear()
        self.setValue(0.0) # дефолтное внутреннее число

    def is_empty(self) -> bool:
        """Динамически проверяет, является ли поле ввода визуально пустым.

        Использует текстовое поле (`lineEdit`) как единственный источник правды 
        (Single Source of Truth), что предотвращает рассинхронизацию состояния UI.

        Returns:
            bool: True, если в поле нет текста (или введены только пробелы), 
                иначе False.
        """
        # Источник правды — физическое текстовое поле ввода внутри спинбокса
        return not self.lineEdit().text().strip()
    
    def stepBy(self, steps: int) -> None:
        """Переопределяет реакцию на изменение значения стрелками или колесиком мыши.

        Если до взаимодействия поле было визуально пустым, оно мгновенно 
        активируется и инициализируется базовым значением 0.0, после чего 
        к нему применяется указанное количество шагов.

        Args:
            steps (int): Количество шагов изменения (положительное при увеличении, 
                отрицательное при уменьшении).
        """
        if self.is_empty():
            self.setValue(0.0)
        super().stepBy(steps)

    def textFromValue(self, value: float) -> str:
        """Определяет строковое представление числа для отображения внутри виджета.

        Переопределяет стандартное форматирование Qt. Если физическое текстовое поле 
        ввода пусто и на виджете нет фокуса ввода, возвращает пустую строку,
        подавляя автоподстановку "0.00".

        Args:
            value (float): Внутреннее числовое значение, хранящееся в спинбоксе.

        Returns:
            str: Пустая строка, если поле не заполнено, или отформатированное 
                строковое представление числа с плавающей точкой.
        """
        if not self.hasFocus() and not super().lineEdit().text().strip():
            return ""
        return super().textFromValue(value)

    def value(self) -> float | None:
        """Возвращает текущее значение виджета с учетом его состояния.

        Returns:
            float | None: Значение типа float, если поле заполнено,
                или None, если поле находится в пустом состоянии.
        """
        if self.is_empty():
            return None
        return super().value()


class FilterPanel(QWidget):
    """Графическая панель управления пресетами, экспортом и фильтрацией данных.

    Класс инкапсулирует пользовательский интерфейс фильтрации и генерации отчетов.
    Он не содержит бизнес-логику фильтрации напрямую, а транслирует действия 
    пользователя в строго типизированные сигналы для внешнего контроллера MainWindow.

    Signals:
        mode_changed (Signal[str]): Генерируется при смене пресета отображения.
            Передает строковый идентификатор режима: "basic", "professional" или "full".
        export_requested (Signal[str]): Генерируется при запросе экспорта данных.
            Передает формат файла, например, "csv".
        refresh_api_requested (Signal[]): Генерируется при нажатии кнопки обновления.
            Сигнализирует о необходимости асинхронной загрузки свежих данных из API ISS.
        apply_filters_requested (Signal[FilterCriteria]): Генерируется при нажатии
            кнопки «Применить». Передает неизменяемый объект критериев фильтрации.
    """

    # Конвенциональные сигналы для связи со слоем управления
    mode_changed: Final = Signal(str)  # Передает: "basic", "professional", "full"
    export_requested: Final = Signal(str)  # Передает: "csv"
    refresh_api_requested: Final = Signal()  # Сигнал на обновление данных из сети
    apply_filters_requested: Final = Signal(FilterCriteria) # Строгая типизация вместо dict

    def __init__(self,parent: QWidget | None = None) -> None:
        """Инициализирует UI-компоненты панели управления.

        Args:
            parent (QWidget | None, optional): Родительский виджет. По умолчанию None.
        """
        super().__init__(parent)

        # Ссылки на UI элементы (будут инициализированы в init_ui)
        self.mode_combo: QComboBox
        self.export_combo: QComboBox
        self.btn_refresh: QPushButton
        self.separator: QFrame
        self.txt_ticker: QLineEdit
        self.txt_name: QLineEdit
        self.spin_price_from: NullableDoubleSpinBox
        self.spin_price_to: NullableDoubleSpinBox
        self.spin_change_from: NullableDoubleSpinBox
        self.spin_change_to: NullableDoubleSpinBox
        self.btn_apply: QPushButton
        self.btn_reset: QPushButton

        self.init_ui()

    def init_ui(self) -> None:
        """Конструирует компоновку (layout) виджетов панели управления и связывает сигналы.

        Создает структуру вложенных слоев (QHBoxLayout, QVBoxLayout), настраивает
        ограничения ввода (длина тикера, диапазоны цен), стилизует разделители
        и подключает методы-обработчики к сигналам элементов интерфейса.
        """
        # Корневой слой панели
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 10)  # Отступ снизу до таблицы

        # Создаем визуальный контейнер QFrame для всей панели
        main_frame = QFrame()
        main_frame.setFrameShape(QFrame.Shape.StyledPanel)
        main_frame.setFrameShadow(QFrame.Shadow.Raised)
        main_layout = QVBoxLayout(main_frame)

        # --- Верхний ряд управления ---
        top_row_layout = QHBoxLayout()

        # Селектор режимов отображения колонок
        top_row_layout.addWidget(QLabel("Режим отображения:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Базовый", userData="basic")
        self.mode_combo.addItem("Профессиональный", userData="professional")
        self.mode_combo.addItem("Сырой JSON (Все поля)", userData="full")
        top_row_layout.addWidget(self.mode_combo)

        # Модуль экспорта в файлы
        top_row_layout.addWidget(QLabel("Экспорт:"))
        self.export_combo = QComboBox()
        self.export_combo.addItem("Экспорт в...", None)
        self.export_combo.addItem("CSV (.csv)", userData="csv")
        top_row_layout.addWidget(self.export_combo)

        # Горизонтальная выравнивающая распорка (Spacer)
        top_row_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        ))

        # Кнопка асинхронного обновления API ISS
        self.btn_refresh = QPushButton("🔄 Обновить данные")
        top_row_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(top_row_layout)

        # --- Разделитель между блоками управления и фильтрами ---
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)  # Горизонтальная линия
        self.separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.separator.setStyleSheet("margin: 5px 0;")  # Отступы сверху и снизу
        main_layout.addWidget(self.separator)

        # --- Нижний ряд ---
        filter_row_layout = QHBoxLayout()

        # Текстовый поиск (SECID и SHORTNAME)
        filter_row_layout.addWidget(QLabel("Тикер:"))
        self.txt_ticker = QLineEdit()
        self.txt_ticker.setPlaceholderText("Напр. SBER")
        self.txt_ticker.setMaxLength(5)
        self.txt_ticker.setFixedWidth(80)
        filter_row_layout.addWidget(self.txt_ticker)

        filter_row_layout.addWidget(QLabel("Название:"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Наименование...")
        filter_row_layout.addWidget(self.txt_name)

        # Интервал цен
        filter_row_layout.addWidget(QLabel("Цена от:"))
        self.spin_price_from = NullableDoubleSpinBox()
        self.spin_price_from.setRange(0.0, 1000000.0)
        self.spin_price_from.clear()
        filter_row_layout.addWidget(self.spin_price_from)
        
        filter_row_layout.addWidget(QLabel("до:"))
        self.spin_price_to = NullableDoubleSpinBox()
        self.spin_price_to.setRange(0.0, 1000000.0)
        self.spin_price_to.clear()
        filter_row_layout.addWidget(self.spin_price_to)

        # Интервал процентов
        filter_row_layout.addWidget(QLabel("Изм. % от:"))
        self.spin_change_from = NullableDoubleSpinBox()
        self.spin_change_from.setRange(-100.0, 100.0)
        self.spin_change_from.clear()
        filter_row_layout.addWidget(self.spin_change_from)

        filter_row_layout.addWidget(QLabel("до:"))
        self.spin_change_to = NullableDoubleSpinBox()
        self.spin_change_to.setRange(-100.0, 100.0)
        self.spin_change_to.clear()
        filter_row_layout.addWidget(self.spin_change_to)

        # Управляющие кнопки фильтрации
        self.btn_apply = QPushButton("🚀 Применить")
        self.btn_apply.setStyleSheet("font-weight: bold;")
        filter_row_layout.addWidget(self.btn_apply)

        self.btn_reset = QPushButton("❌ Сбросить")
        filter_row_layout.addWidget(self.btn_reset)

        main_layout.addLayout(filter_row_layout)
        root_layout.addWidget(main_frame)

        # Автоматическое подключение обработчиков стилей
        self.txt_ticker.textChanged.connect(self._on_ticker_changed)
        self.txt_name.textChanged.connect(self._on_name_changed)
        
        self.spin_price_from.valueChanged.connect(self._on_price_from_changed)
        self.spin_price_to.valueChanged.connect(self._on_price_to_changed)
        self.spin_change_from.valueChanged.connect(self._on_change_from_changed)
        self.spin_change_to.valueChanged.connect(self._on_change_to_changed)


        # Сигнально-слотовая архитектура событий нажатия
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.export_combo.currentIndexChanged.connect(self._on_export_changed)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.btn_reset.clicked.connect(self._on_reset_clicked)

    @Slot(str)
    def _on_ticker_changed(self, text: str) -> None:
        """Слот обработки изменения текста в поле ввода тикера.
        
        Срабатывает при вводе/удалении символов. Логирует текущее значение,
        после чего инициирует перерисовку QSS-стилей для виджета.

        Args:
            text (str): Актуальный текст из поля ввода тикера.
        """
        logger.debug(
            "Слот _on_ticker_changed вызван. Текущий текст: '{text}'", text=text)
        self._update_widget_style(self.txt_ticker)

    @Slot(str)
    def _on_name_changed(self, text: str) -> None:
        """Слот обработки изменения текста в поле ввода названия компании."""
        logger.debug("Слот _on_name_changed вызван. Текущий текст: '{text}'", text=text)
        self._update_widget_style(self.txt_name)

    @Slot(float)
    def _on_price_from_changed(self, value: float) -> None:
        """Слот обработки изменения нижней границы стоимости ценной бумаги.

        Args:
            value (float): Новое численное значение из спинбокса. 
                Примечание: если поле визуально очищено, сигнал valueChanged 
                все равно передаст float (0.0), но метод ценности виджета 
                .value() вернет None благодаря нашей кастомной логике.
        """
        # Опрашиваем реальное бизнес-значение (может быть float или None)
        actual_value = self.spin_price_from.value()
        logger.debug(
            "Слот _on_price_from_changed вызван. Значение сигнала: {value}, "
            "Бизнес-значение: {actual_value}", 
            value=value, 
            actual_value=actual_value,
        )
        self._update_widget_style(self.spin_price_from)

    @Slot(float)
    def _on_price_to_changed(self, value: float) -> None:
        """Слот обработки изменения верхней границы стоимости ценной бумаги."""
        actual_value = self.spin_price_to.value()
        logger.debug(
            "Слот _on_price_to_changed вызван. Значение сигнала: {value}, "
            "Бизнес-значение: {actual_value}", 
            value=value, 
            actual_value=actual_value
        )
        self._update_widget_style(self.spin_price_to)

    @Slot(float)
    def _on_change_from_changed(self, value: float) -> None:
        """Слот обработки изменения минимального процента отклонения цены."""
        actual_value = self.spin_change_from.value()
        logger.debug(
            "Слот _on_change_from_changed вызван. Значение сигнала: {value}, "
            "Бизнес-значение: {actual_value}", 
            value=value, 
            actual_value=actual_value
        )
        self._update_widget_style(self.spin_change_from)

    @Slot(float)
    def _on_change_to_changed(self, value: float) -> None:
        """Слот обработки изменения максимального процента отклонения цены."""
        actual_value = self.spin_change_to.value()
        logger.debug(
            "Слот _on_change_to_changed вызван. "
            "Значение сигнала:  {value}, Бизнес-значение: {actual_value}", 
            value=value, 
            actual_value=actual_value
        )
        self._update_widget_style(self.spin_change_to)

    def _update_widget_style(self, widget: QWidget | None = None) -> None:
        """Динамически обновляет CSS/QSS свойства переданного виджета.

        Проверяет валидность объекта и перерисовывает его на основе текущего
        состояния активности (динамическое свойство 'active'). Если переданный
        объект равен None или не является экземпляром QWidget, выполнение
        прерывается.

        Args:
            widget: Целевой графический виджет для обновления стиля.
                По умолчанию равен None.

        Returns:
            None. Метод выполняет только графическое обновление объекта.
        """
        if not widget or not isinstance(widget, QWidget):
            logger.debug(
                "Метод _update_widget_style вызван с некорректным объектом: {widget}", 
                widget=widget
            )
            return

        is_active: bool = self._is_widget_active(widget)

        logger.debug(
            "Обновление стиля для виджета '{}' (objectName: '{}'). Статус active -> {}",
            widget.__class__.__name__,
            widget.objectName(),
            is_active,
        )
        
        widget.setProperty("active", is_active)

        # Перерисовка стилей в Qt-подсистеме
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    
    def _is_widget_active(self, widget: QWidget) -> bool:
        """Вспомогательный метод для определения активности фильтра.

        Args:
            widget (QWidget): Проверяемый графический элемент.

        Returns:
            bool: True, если в поле введены значимые данные.
        """
        # Для текстовых полей: активны, если строка не пустая после удаления пробелов
        if widget in (self.txt_ticker, self.txt_name):
            res_text = bool(widget.text().strip())
            logger.debug(
                "Проверка текстового виджета {}: active={}", 
                widget.objectName(), 
                res_text,
            )
            return res_text

        # Для спинбоксов опрашиваем их собственный метод инверсивно
        if isinstance(widget, NullableDoubleSpinBox):
            res_spin = not widget.is_empty()
            logger.debug("Проверка числового спинбокса {}: active={}", widget.objectName(), res_spin)
            return res_spin

        logger.warning(
            "Методу _is_widget_active передан неизвестный тип виджета: {}", 
            widget.__class__.__name__
        )
        return False


    def get_filter_params(self) -> FilterCriteria:
        """Конвейер сборки параметров: считывает и очищает данные из полей GUI.

        Returns:
            FilterCriteria: Строго структурированный контейнер параметров.
        """
        criteria = FilterCriteria(
            ticker=self.txt_ticker.text().strip().upper() or None,
            name=self.txt_name.text().strip() or None,
            price_from=self.spin_price_from.value(),
            price_to=self.spin_price_to.value(),
            change_from=self.spin_change_from.value(),
            change_to=self.spin_change_to.value(),
        )
        
        # Логируем на уровне INFO успешную агрегацию параметров
        logger.info("Сформирован новый объект критериев фильтрации: {}", criteria)
        return criteria

    @Slot()
    def _on_apply_clicked(self) -> None:
        """Обрабатывает нажатие кнопки 'Фильтр'.

        Собирает текущие параметры фильтрации из элементов интерфейса и отправляет
        их через сигнал `apply_filters_requested`.

        Raises:
            RuntimeError: При ошибке сборки параметров или отправки сигнала.
        """
        try:
            criteria = self.get_filter_params()
            logger.info(f"Пользователь применил фильтры: {criteria}")
            self.apply_filters_requested.emit(criteria)
        except Exception as e:
            logger.exception("Критический сбой сборки параметров фильтрации")
            raise RuntimeError("Сбой при фильтрации данных") from e

    @Slot()
    def _on_reset_clicked(self) -> None:
        """Выполняет полный сброс всех полей панели в исходное состояние.

        Очищает текстовые поля, сбрасывает числовые диапазоны до минимума, обновляет
        стили виджетов и возвращает выпадающий список режимов к начальному элементу.
        В конце отправляет сигнал с пустыми критериями для обновления таблицы.

        Raises:
            RuntimeError: При сбое графической подсистемы в процессе сброса.
        """
        logger.info("Пользователь инициировал полный сброс панели фильтров")

        # Блокируем сигналы ВСЕХ важных элементов на время сброса
        widgets_to_block: Final = (
            self,
            self.mode_combo,
            self.spin_price_from,
            self.spin_price_to,
            self.spin_change_from,
            self.spin_change_to,
        )
        
        for w in widgets_to_block:
            w.blockSignals(True)

        try:
            # Мягкая очистка полей
            self.txt_ticker.clear()
            self.txt_name.clear()

            # Сброс числовых диапазонов в базовое состояние
            self.spin_price_from.clear()
            self.spin_price_to.clear()
            self.spin_change_from.clear()
            self.spin_change_to.clear()

            # Принудительно сбрасываем стили (свойства active) для всех полей
            for widget in (
                self.txt_ticker, 
                self.txt_name, 
                self.spin_price_from,
                self.spin_price_to, 
                self.spin_change_from, 
                self.spin_change_to,
            ):
                self._update_widget_style(widget)
        except Exception as e:
            logger.exception("Ошибка при выполнении сброса параметров интерфейса")
            raise RuntimeError("Сбой графической подсистемы при сбросе настроек") from e
        finally:
            # Гарантированно возвращаем обработку сигналов в исходное состояние
            for w in widgets_to_block:
                w.blockSignals(False)
        
        # Эмитим сигнал с пустыми критериями, чтобы обновить представление (View)
        self.apply_filters_requested.emit(
            FilterCriteria(None, None, None, None, None, None)
        )

    @Slot(int)
    def _on_mode_changed(self, index: int) -> None:
        """Обрабатывает изменение режима отображения в выпадающем списке.

        Извлекает технический идентификатор режима из userData выбранного элемента
        и отправляет его через сигнал `mode_changed`.

        Args:
            index: Порядковый индекс выбранного элемента в `mode_combo`.

        Raises:
            RuntimeError: При возникновении любой внутренней ошибки во время
                обработки изменения режима.
        """
        try:
            technical_mode: ViewMode = self.mode_combo.itemData(index)

            if technical_mode:
                logger.debug(
                    "Смена режима отображения на: '{}' (индекс: {})",
                    technical_mode,
                    index,
                )
                self.mode_changed.emit(technical_mode)
            else:
                logger.warning("Получен пустой режим userData для индекса {}", index)
        except Exception as e:
            logger.exception(
                "Ошибка при обработке изменения режима отображения (индекс: {})", index
            )
            raise RuntimeError(
                "Сбой графического интерфейса при смене режима фильтрации"
            ) from e

    @Slot(int)
    def _on_export_changed(self, index: int) -> None:
        """Обрабатывает выбор формата для экспорта данных.

        Проверяет выбранный формат. Если выбран формат 'csv', генерирует сигнал
        `export_requested` и сбрасывает состояние выпадающего списка к первому
        элементу, временно блокируя сигналы виджета для предотвращения рекурсии.

        Args:
            index: Порядковый индекс выбранного элемента в `export_combo`.

        Raises:
            RuntimeError: При возникновении критической ошибки в процессе
                инициализации экспорта.
        """
        try:
            technical_format: ExportFormat = self.export_combo.itemData(index)

            if technical_format == "csv":
                logger.info("Запрошен экспорт данных в формат CSV")
                self.export_requested.emit("csv")

                # Временно блокируем сигналы, чтобы сброс индекса не вызвал метод заново
                self.export_combo.blockSignals(True)
                self.export_combo.setCurrentIndex(0)
                self.export_combo.blockSignals(False)  # Возвращаем отслеживание обратно
        except Exception as e:
            logger.exception(
                "Ошибка при обработке запроса на экспорт (индекс: {})", index
            )
            raise RuntimeError(
                "Сбой графического интерфейса при экспорте данных"
            ) from e

    @Slot()
    def _on_refresh_clicked(self) -> None:
        """Обрабатывает нажатие кнопки обновления данных.

        Генерирует сигнал `refresh_api_requested` для уведомления приложения
        о необходимости перезагрузить данные из внешнего API.

        Raises:
            RuntimeError: При сбое во время отправки сигнала обновления.
        """
        try:
            logger.info("Пользователь нажал кнопку обновления API данных")

            self.refresh_api_requested.emit()
        except Exception as e:
            logger.exception("Ошибка при генерации сигнала обновления данных API")
            raise RuntimeError(
                "Сбой графического интерфейса при попытке обновить данные"
            ) from e
