import pytest
from PySide6.QtCore import Qt, QLocale
from src.views.filter_panel import FilterCriteria, FilterPanel


def test_filter_panel_default_state(filter_panel):
    """Тест: Проверка исходного состояния панели при запуске."""
    assert filter_panel.txt_ticker.text() == ""
    assert filter_panel.txt_name.text() == ""
    assert filter_panel.spin_change_from.value() == None
    assert filter_panel.spin_change_to.value() == None
    assert filter_panel.mode_combo.currentIndex() == 0
    assert filter_panel.export_combo.currentIndex() == 0


def test_filter_panel_ux_highlighting(filter_panel, qtbot):
    """Тест: Проверка реактивности UI/UX (динамическая смена QSS свойства 'active')."""
    assert filter_panel._is_widget_active(filter_panel.txt_ticker) is False

    qtbot.keyClicks(filter_panel.txt_ticker, "SBER")

    assert filter_panel._is_widget_active(filter_panel.txt_ticker) is True
    assert filter_panel.txt_ticker.property("active") is True


def test_filter_panel_apply_pipeline(qtbot):
    """Тест : Тест нажатия 'Применить' и валидации словаря параметров."""
    # Создаем и регистрируем виджет панели в pytest-qt
    panel = FilterPanel()
    qtbot.addWidget(panel)
    panel.show()  # Важно: виджет должен быть показан, чтобы геометрия и фокус работали
    
    # --- ЭМУЛЯЦИЯ ЗАПОЛНЕНИЯ ПОЛЯ "ЦЕНА ОТ" ---
    
    # 1. Переводим фокус напрямую на внутренний lineEdit числового поля
    # Это заставит hasFocus() внутри textFromValue отрабатывать корректно
    panel.spin_price_from.lineEdit().setFocus()
    
    # 2. Очищаем дефолтное состояние (если необходимо)
    panel.spin_price_from.lineEdit().clear()
    
    # 3. Печатаем значение через qtbot прямо во внутреннее текстовое поле
    # Так мы физически наполняем Single Source of Truth текстом
    decimal_separator = QLocale().decimalPoint()
    value_str = f"150{decimal_separator}5"
    
    # 3. Печатаем строку с правильным системным разделителем
    qtbot.keyClicks(panel.spin_price_from.lineEdit(), value_str)
    
    # 4. Программно подтверждаем ввод (симулируем нажатие Enter или потерю фокуса)
    # Это синхронизирует строковое значение lineEdit с внутренним value() в Qt
    qtbot.keyPress(panel.spin_price_from.lineEdit(), Qt.Key.Key_Enter)
    
    # --- ЭМУЛЯЦИЯ ЗАПОЛНЕНИЯ ПОЛЯ "ТИКЕР" (для полноты пайплайна) ---
    panel.txt_ticker.setFocus()
    qtbot.keyClicks(panel.txt_ticker, "GAZP")
    
    # --- НАЖАТИЕ КНОПКИ ПРИМЕНИТЬ ---
    qtbot.mouseClick(panel.btn_apply, Qt.MouseButton.LeftButton)
    
    # --- ПРОВЕРКА КРИТЕРИЕВ ---
    criteria = panel.get_filter_params()

    assert criteria.ticker == "GAZP"
    assert criteria.price_from == 150.5000
    assert criteria.change_to == None
    assert criteria.change_from == None
    assert criteria.name is None
    assert criteria.price_to == None


def test_filter_panel_intellectual_reset(filter_panel, qtbot):
    """Тест: Проверка кнопки 'Сбросить' — очистка UI и сброс таблицы."""
    filter_panel.txt_ticker.setText("LKOH")
    filter_panel.spin_price_to.setValue(5000.0)
    filter_panel.spin_change_from.setValue(2.5)
    filter_panel.mode_combo.setCurrentIndex(1)

    with qtbot.waitSignal(
        filter_panel.apply_filters_requested, timeout=1000
    ) as blocker:
        qtbot.mouseClick(filter_panel.btn_reset, Qt.MouseButton.LeftButton)

    # проверяем, что интерфейс обнулился
    assert filter_panel.txt_ticker.text() == ""
    assert filter_panel.spin_price_to.value() == None
    assert filter_panel.spin_price_from.value() == None
    assert filter_panel.spin_change_from.value() == None
    assert filter_panel.spin_change_to.value() == None

    criteria: FilterCriteria = blocker.args[0]

    # При сбросе все поля критериев должны стать None
    assert criteria.ticker is None
    assert criteria.name is None
    assert criteria.price_from is None
    assert criteria.price_to is None
    assert criteria.change_from is None
    assert criteria.change_to is None


@pytest.mark.parametrize(
    "combo_index, expected_mode",
    [
        (0, "basic"),
        (1, "professional"),
        (2, "full"),
    ],
)
def test_filter_panel_mode_combobox(filter_panel, qtbot, combo_index, expected_mode):
    """Тест: Параметризванная проверка переключения режимов отображения таблицы."""
    if filter_panel.mode_combo.currentIndex() == combo_index:
        # Если целевой индекс 0, уводим индекс к 1, чтобы вызвался сигнал mode_changed
        alternative_index = 1 if combo_index == 0 else 0
        filter_panel.mode_combo.setCurrentIndex(alternative_index)

    with qtbot.waitSignal(filter_panel.mode_changed, timeout=1000) as blocker:
        filter_panel.mode_combo.setCurrentIndex(combo_index)

    assert blocker.args[0] == expected_mode
