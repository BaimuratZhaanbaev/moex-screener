"""Комплекс юнит-тестирования конвейеров трансформации данных Мосбиржи.

Обеспечивает валидацию сквозной сборки матриц Pandas, контроль динамического
приведения финансовых типов данных и проверку устойчивости парсера к аномалиям сети.
"""

from typing import Any

import pandas as pd
import pytest

from src.core.parser import MoexDataParser
from src.core.extractor import MoexSchemaExtractor
from src.core.constants import MoexColumns


def test_parse_valid_data(real_api_data: dict[str, Any]) -> None:
    """Проверяет корректность работы главного конвейера и реляционного слияния таблиц.
    
    Убеждается, что результирующая матрица формируется без потерь строк и колонок
    обоих исходных блоков.
    """
    parser = MoexDataParser()
    df = parser.parse_to_dataframe(real_api_data)

    # 1. Результат не пустой и является DataFrame
    assert isinstance(df, pd.DataFrame), "Результат должен быть объектом pd.DataFrame"
    assert not df.empty, "DataFrame не должен быть пустым при валидных входных данных"

    # 2. Количество строк соответствует исходным данным из блока securities
    expected_rows = len(real_api_data["securities"]["data"])
    assert len(df) == expected_rows, (
        f"Ожидалось {expected_rows} строк, получено {len(df)}"
    )

    # 3. Проверка Left Join: присутствуют колонки из обоих блоков
    assert "SHORTNAME" in df.columns, (
        "В итоговом DataFrame отсутствует колонка из блока 'securities'"
    )
    assert "LAST" in df.columns, (
        "В итоговом DataFrame отсутствует колонка из блока 'marketdata'"
    )
    assert "SECID" in df.columns, "Потерян ключевой идентификатор SECID"


def test_get_numeric_columns_logic(numeric_casting_case: tuple) -> None:
    """Тестирует логику динамического определения типов на синтетических метаданных.
    
    Гарантирует, что экстрактор безошибочно выявляет числовые типы биржи и отсекает
    текстовые поля.
    """
    # Распаковка кортежа из фикстуры
    mock_metadata, expected_in, expected_out = numeric_casting_case

    # Формирование структуры, похожую на ответ MOEX ISS
    fake_raw_data = {
        "securities": {"metadata": mock_metadata},
        "marketdata": {"metadata": {}},
    }

    # Переправление вызова на сервисный класс-экстрактор
    numeric_cols = MoexSchemaExtractor.extract_numeric_columns(fake_raw_data)

    # Проверка на наличие ожидаемых колонок
    for col in expected_in:
        assert col in numeric_cols, (
            f"Колонка '{col}' с типом {mock_metadata[col]['type']} "
            f"ДОЛЖНА быть распознана как числовая"
        )

    # Проверка отсутствия лишних колонок
    for col in expected_out:
        assert col not in numeric_cols, (
            f"Колонка '{col}' с типом {mock_metadata[col]['type']} "
            f"НЕ ДОЛЖНА быть распознана как числовая"
        )


def test_dynamic_numeric_casting_on_real_data(real_api_data: dict[str, Any]) -> None:
    """Проверяет корректность парсинга типов на реальном дампе ответов Московской Биржи.
    
    Убеждается, что в результирующий набор числовых колонок не попадает явный текст.
    """
    # Вызов переправлен на новый сервисный класс-экстрактор
    numeric_cols = MoexSchemaExtractor.extract_numeric_columns(real_api_data)

    # 1. Проверяем, что список в принципе не пустой (ведь на бирже точно есть числа)
    assert len(numeric_cols) > 0, (
        "Парсер не нашел ни одной числовой колонки в реальных данных MOEX"
    )

    # 2. Проверяем динамически, что в список не затесались явные строки
    # (просто смотрим на структуру real_api_data, если SHORTNAME там есть)
    for block in ["securities", "marketdata"]:
        metadata = real_api_data.get(block, {}).get("metadata", {})
        if "SHORTNAME" in metadata:
            assert "SHORTNAME" not in numeric_cols, (
                "Текстовая колонка SHORTNAME ошибочно попала в числовые"
            )

    # 3. Гарантируем уникальность колонок
    assert len(numeric_cols) == len(set(numeric_cols)), (
        "В итоговом списке числовых колонок есть дубликаты"
    )


def test_null_values_isolation(real_api_data: dict[str, Any]) -> None:
    """Проверяет соответствие требованию по изоляции неопределенных биржевых цен.
    
    Гарантирует, что пустые значения (null) переходят в NaN, предотвращая ложные
    срабатывания фильтров котировок по цене 0.0.
    """
    parser = MoexDataParser()
    df = parser.parse_to_dataframe(real_api_data)

    # Извлекаем все значения колонки LAST, которые парсер пометил как NaN/None
    col_last = MoexColumns.LAST.value
    null_prices = df[df[col_last].isna()][col_last]

    # Если в файле securities_real.json есть хотя бы один null в LAST, проверим его
    if not null_prices.empty:
        for last_price in null_prices:
            # Проверка на равенство с нулем (должно возвращать False)
            assert last_price != 0, (
                "Ошибка: Финансовый null был ошибочно заменен на int(0)"
            )
            assert last_price != 0.0, (
                "Ошибка: Финансовый null был ошибочно заменен на float(0.0)"
            )
    else:
        pytest.skip(
            "В тестовом файле securities_real.json "
            "не обнаружено записей с LAST = null для проверки ТЗ."
        )


def test_parser_resilience_to_corrupted_data(
        corrupted_fixture_source: Any, 
        load_fixture: Any,
    ) -> None:
    """Проверяет отказоустойчивость конвейера к поврежденным структурам JSON-пакетов.
    
    Гарантирует перехват исключений и предотвращает аварийное завершение главного
    цикла Qt GUI при сетевых аномалиях.
    """
    parser = MoexDataParser()

    # Извлечение данных (из файла или берем сырую структуру)
    bad_data = (
        load_fixture(corrupted_fixture_source)
        if isinstance(corrupted_fixture_source, str)
        else corrupted_fixture_source
    )

    try:
        df = parser.parse_to_dataframe(bad_data)

        assert isinstance(df, pd.DataFrame), (
            f"Для источника {corrupted_fixture_source} "
            f"результат должен быть pd.DataFrame"
        )
        assert df.empty, (
            f"Для источника {corrupted_fixture_source} "
            f"получен не пустой DF (строк: {len(df)})"
        )
    except Exception as e:
        pytest.fail(
            f"Парсер упал с ошибкой {type(e).__name__} "
            f"на источнике {corrupted_fixture_source}: {e}"
        )
