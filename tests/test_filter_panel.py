import pytest
from PySide6.QtCore import Qt


def test_filter_panel_default_state(filter_panel):
    """Тест: Проверка исходного состояния панели при запуске."""
    assert filter_panel.ticker_input.text() == ""
    assert filter_panel.name_input.text() == ""
    assert filter_panel.price_from.value() == filter_panel.price_from.minimum()
    assert filter_panel.change_from.value() == filter_panel.change_from.minimum()
    assert filter_panel.mode_combo.currentIndex() == 0
    assert filter_panel.export_combo.currentIndex() == 0


def test_filter_panel_ux_highlighting(filter_panel, qtbot):
    """Тест: Проверка реактивности UI/UX (динамическая смена QSS свойства 'active')."""
    assert filter_panel._is_widget_active(filter_panel.ticker_input) is False
    
    qtbot.keyClicks(filter_panel.ticker_input, "SBER")
    
    assert filter_panel._is_widget_active(filter_panel.ticker_input) is True
    assert filter_panel.ticker_input.property("active") is True


def test_filter_panel_apply_pipeline(filter_panel, qtbot):
    """Тест : Тест нажатия 'Применить' и валидации словаря параметров."""
    qtbot.keyClicks(filter_panel.ticker_input, "GAZP")
    filter_panel.price_from.setValue(150.5000)
    filter_panel.change_to.setValue(5.25)
    
    # перехватчик сигналов Qt
    with qtbot.waitSignal(filter_panel.apply_filters_requested, timeout=1000) as blocker:
        qtbot.mouseClick(filter_panel.apply_btn, Qt.MouseButton.LeftButton)
        
    # Проверяем, что сигнал улетел и принес правильный словарь
    assert blocker.signal_triggered is True

    emitted_dict = blocker.args[0]
    
    assert emitted_dict["SECID"] == "GAZP"
    assert emitted_dict["price_from"] == 150.5000
    assert emitted_dict["change_to"] == 5.25
    assert emitted_dict["SHORTNAME"] is None
    assert emitted_dict["price_to"] is None
    assert emitted_dict["change_from"] is None


def test_filter_panel_intellectual_reset(filter_panel, qtbot):
    """Тест: Проверка кнопки 'Сбросить' — очистка UI и сброс таблицы."""
    filter_panel.ticker_input.setText("LKOH")
    filter_panel.price_to.setValue(5000.0)
    filter_panel.mode_combo.setCurrentIndex(1)
    
    with qtbot.waitSignal(filter_panel.apply_filters_requested, timeout=1000) as blocker:
        qtbot.mouseClick(filter_panel.reset_btn, Qt.MouseButton.LeftButton)
        
    # проверяем, что интерфейс обнулился и отправился пустой словарь
    assert filter_panel.ticker_input.text() == ""
    assert filter_panel.price_to.value() == filter_panel.price_to.minimum()
    assert filter_panel.mode_combo.currentIndex() == 0
    
    emitted_dict = blocker.args[0]

    assert all(value is None for value in emitted_dict.values())


@pytest.mark.parametrize(
    "combo_index, expected_mode",
    [
        (0, "basic"),
        (1, "professional"),
        (2, "full"),
    ]
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
    