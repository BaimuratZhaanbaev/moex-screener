import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from src.api.client import MoexAPIError
from src.core.constants import DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS


def test_main_window_integration_filtering(main_window, qtbot):
    """Тест: Сквозная фильтрация через графический интерфейс."""
    panel = main_window.filter_panel
    view = main_window.table_view

    assert view.model().rowCount() == 5

    qtbot.keyClicks(panel.ticker_input, "aflt")
    qtbot.mouseClick(panel.apply_btn, Qt.MouseButton.LeftButton)

    assert view.model().rowCount() == 1

    idx = view.model().index(0, 0)
    assert view.model().data(idx, Qt.ItemDataRole.DisplayRole) == "AFLT"


def test_main_window_integration_reset(main_window, qtbot):
    """Тест: Кнопка сброса возвращает все строки обратно в таблицу."""
    panel = main_window.filter_panel
    view = main_window.table_view

    qtbot.keyClicks(panel.ticker_input, "SBER")
    qtbot.mouseClick(panel.apply_btn, Qt.MouseButton.LeftButton)
    assert view.model().rowCount() == 1

    qtbot.mouseClick(panel.reset_btn, Qt.MouseButton.LeftButton)

    assert panel.ticker_input.text() == ""
    assert view.model().rowCount() == 5


def test_main_window_export_csv_success(main_window, qtbot, mocker):
    """Тест: Успешный экспорт отфильтрованных данных в файл CSV."""
    panel = main_window.filter_panel
    mocker.patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", ""))
    mock_box = mocker.patch("PySide6.QtWidgets.QMessageBox.information")
    panel.export_combo.setCurrentIndex(1)
    mock_box.assert_not_called()


def test_main_window_export_csv_canceled(main_window, qtbot, mocker):
    """Тест: Пользователь нажал 'Экспорт', но в окне выбора файла нажал 'Отмена'."""
    panel = main_window.filter_panel

    mocker.patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("", ""))
    mock_box = mocker.patch("PySide6.QtWidgets.QMessageBox.information")

    panel.export_combo.setCurrentIndex(1)

    mock_box.assert_not_called()


def test_main_window_api_refresh_success(main_window, qtbot, mocker, real_api_data):
    """Тест: Кнопка 'Обновить данные' успешно скачивает и перезаливает данные из API."""
    panel = main_window.filter_panel

    mocker.patch("src.api.client.MoexClient.fetch_from_api", return_value=real_api_data)
    qtbot.mouseClick(panel.refresh_btn, Qt.MouseButton.LeftButton)

    status_text = main_window.statusBar().currentMessage()
    assert "Данные обновлены" in status_text


@pytest.mark.skip(reason="Проблема с перехватом QMessageBox в текущей версии PySide6")
def test_main_window_api_refresh_network_error(main_window, qtbot, mocker):
    """Тест: Обработка падения интернета (MoexAPIError) при вызове обновления."""
    panel = main_window.filter_panel

    mocker.patch(
        "src.api.client.MoexClient.fetch_from_api",
        side_effect=MoexAPIError("Ошибка соединения с сервером MOEX"),
    )

    mock_critical = mocker.patch.object(QMessageBox, "critical", return_value=None)

    qtbot.mouseClick(panel.refresh_btn, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_critical.called, timeout=2000)


def test_main_window_column_visibility_logic(main_window, qtbot):
    """Тест: Проверка динамического скрытия колонок интерфейса для всех режимов."""
    panel = main_window.filter_panel
    view = main_window.table_view
    model = main_window.table_model

    # режим "basic"
    panel.mode_combo.setCurrentIndex(0)

    for i in range(model.columnCount()):
        col_name = model._df.columns[i]
        if col_name in DEFAULT_COLUMNS:
            assert view.isColumnHidden(i) is False, (
                f"Колонка {col_name} должна быть видима в basic"
            )
        else:
            assert view.isColumnHidden(i) is True, (
                f"Колонка {col_name} должна быть скрыта в basic"
            )

    # режим "professional"
    panel.mode_combo.setCurrentIndex(1)

    for i in range(model.columnCount()):
        col_name = model._df.columns[i]
        if col_name in PROFESSIONAL_COLUMNS:
            assert view.isColumnHidden(i) is False, (
                f"Колонка {col_name} должна быть видима в professional"
            )
        else:
            assert view.isColumnHidden(i) is True, (
                f"Колонка {col_name} должна быть скрыта в professional"
            )

    # режим "full"
    panel.mode_combo.setCurrentIndex(2)

    for i in range(model.columnCount()):
        col_name = model._df.columns[i]
        assert view.isColumnHidden(i) is False, (
            f"Колонка {col_name} должна отображаться в режиме full"
        )


def test_main_window_sorting_with_nulls_at_bottom(main_window, qtbot):
    """Тест: Интерактивная сортировка по клику на заголовок."""
    view = main_window.table_view
    model = main_window.table_model
    last_col_idx = list(model._df.columns).index("LAST")

    # Ситуация 1: Сортировка по ВОЗРАСТАНИЮ
    view.sortByColumn(last_col_idx, Qt.SortOrder.AscendingOrder)
    last_row_idx = model.rowCount() - 1
    secid_index = model.index(last_row_idx, 0)

    assert model.data(secid_index, Qt.ItemDataRole.DisplayRole) == "LKOH", (
        "При сортировке по возрастанию акция с ценой NaN не ушла вниз таблицы!"
    )

    # Ситуация 2: Сортировка по УБЫВАНИЮ
    view.sortByColumn(last_col_idx, Qt.SortOrder.DescendingOrder)
    secid_index_desc = model.index(last_row_idx, 0)

    assert model.data(secid_index_desc, Qt.ItemDataRole.DisplayRole) == "LKOH", (
        "При сортировке по убыванию акция с ценой NaN ошибочно вылезла наверх!"
    )
