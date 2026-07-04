from src.core.analytics import DataFilterService


def test_ticker_filter_case_insensitive(reference_market_data):
    """Тест: Фильтрация по тикеру должна быть регистронезависимой."""
    # В эталоне есть "gaZp". Ищем строчными буквами "gazp"
    res = DataFilterService.filter_market_data(reference_market_data, ticker="gazp")

    assert len(res) == 1
    # Проверяем, что нашелся именно Газпром, игнорируя регистр букв
    assert res.iloc[0]["SECID"] == "gaZp"


def test_name_filter_partial_match(reference_market_data):
    """Тест: Фильтрация по названию по частично совпадающей подстроке."""
    # Ищем подстроку "ао"
    res = DataFilterService.filter_market_data(reference_market_data, name="ао")
    secids = res["SECID"].values

    assert len(res) == 2
    assert "gaZp" in secids
    assert "VTBR" in secids


def test_price_range_filtering_and_null_exclusion(reference_market_data):
    """Тест: Диапазон цен [100; 300] должен включать границы и отсекать NaN."""
    # Ожидаем: SBER (250.5), GAZP (120.0), AFLT (100.0), FixP (299.9)
    # LKOH (NaN) должен отсечься автоматически, так как NaN не равен 0 и не число
    res = DataFilterService.filter_market_data(
        df=reference_market_data, price_from=100.0, price_to=300.0
    )

    assert len(res) == 4
    assert "LKOH" not in res["SECID"].values
    assert "AFLT" in res["SECID"].values  # Граничное значение прошло успешно


def test_strict_zero_change_vs_null(reference_market_data):
    """Тест: Поиск строго нулевого изменения не должен захватывать null."""
    # Ищем изменение цены строго равное 0.0%
    res = DataFilterService.filter_market_data(
        df=reference_market_data, change_from=0.0, change_to=0.0
    )

    # Должна остаться только ROSN (изменение 0.0)
    # LKOH (NaN) обязан отсечься
    assert len(res) == 1
    assert res.iloc[0]["SECID"] == "ROSN"
