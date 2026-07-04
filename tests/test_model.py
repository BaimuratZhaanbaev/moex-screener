from PySide6.QtCore import Qt


def test_qt_model_dimensions(initialized_qt_model, reference_market_data):
    """Тест: Размерность модели должна строго соответствовать эталону."""
    assert initialized_qt_model.rowCount() == len(reference_market_data)
    # Количество колонок в модели должно совпадать с датафреймом
    assert initialized_qt_model.columnCount() == len(reference_market_data.columns)


def test_qt_model_header_mapping(initialized_qt_model):
    """Тест: Технические колонки должны заменяться на русские заголовки из config."""
    # Колонка 0 в эталоне — это "SECID". Она должна превратиться в "Тикер"
    header_text = initialized_qt_model.headerData(
        0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
    )

    assert header_text == "Тикер"


def test_qt_model_null_visual_display(initialized_qt_model):
    """Тест: Биржевой null (NaN) должен отображаться в интерфейсе как прочерк '-'."""
    # В эталоне LKOH имеет индекс строки 2. Колонка LAST имеет индекс 2.
    # Проверяем ячейку цены Лукойла (там np.nan)
    index_nan = initialized_qt_model.index(2, 2)
    display_value = initialized_qt_model.data(index_nan, Qt.ItemDataRole.DisplayRole)

    assert display_value == "-"


def test_qt_model_sorting_keeps_null_at_bottom(initialized_qt_model):
    """Тест: na_position='last' держит null внизу при любом порядке."""
    # Индекс колонки LAST = 2.

    # 1. Сортируем ПО ВОЗРАСТАНИЮ
    initialized_qt_model.sort(2, Qt.SortOrder.AscendingOrder)
    last_row_index = initialized_qt_model.rowCount() - 1

    assert initialized_qt_model._df.iloc[last_row_index]["SECID"] == "LKOH"

    # 2. Сортируем ПО УБЫВАНИЮ
    initialized_qt_model.sort(2, Qt.SortOrder.DescendingOrder)
    last_row_index = initialized_qt_model.rowCount() - 1

    assert initialized_qt_model._df.iloc[last_row_index]["SECID"] == "LKOH"
