import json
from pathlib import Path

import pandas as pd
import pytest
from loguru import logger

from src.models.table_model import MoexTableModel


@pytest.fixture(autouse=True)
def caplog_for_loguru(caplog):
    """Автоматически перенаправляет логи из loguru в стандартный caplog от pytest."""
    # Удаляем дефолтный обработчик loguru и перенаправляем вывод в caplog
    handler_id = logger.add(caplog.handler, format="{message}", level=0)
    yield
    logger.remove(handler_id)


# Базовый путь к фикстурам
FIXTURES_DIR = Path(__file__).parents[1] / "data" / "fixtures"


@pytest.fixture
def load_fixture():
    """Фабрика-фикстура для динамической загрузки любого JSON по имени файла."""

    def _load(source: str) -> dict:
        # Если на вход подан готовый словарь
        if isinstance(source, dict):
            return source

        # Если на вход подана строка, трактуем её как имя файла
        file_path = FIXTURES_DIR / source
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    return _load


@pytest.fixture
def real_api_data(load_fixture):
    """Фикстура, отдающая готовый словарь из securities_real.json."""
    return load_fixture("securities_real.json")


@pytest.fixture(
    params=[
        # Case 1: Все числовые типы
        (
            {
                "VALTODAY": {"type": "int64"},
                "LAST": {"type": "double"},
                "OPEN": {"type": "float"},
                "VOLUME": {"type": "int32"},
            },
            ["VALTODAY", "LAST", "OPEN", "VOLUME"],
            [],
        ),
        # Case 2: Нечисловые типы
        (
            {
                "SHORTNAME": {"type": "string"},
                "SECID": {"type": "string"},
                "TRADEDATE": {"type": "date"},
            },
            [],
            ["SHORTNAME", "SECID", "TRADEDATE"],
        ),
        # Case 3: Проверка регистра
        (
            {
                "HIGH": {"type": "Double"},
                "LOW": {"type": "INT32"},
            },
            ["HIGH", "LOW"],
            [],
        ),
    ],
    ids=["all_numeric_types", "non_numeric_types", "case_insensitivity"],
)
def numeric_casting_case(request):
    """Фикстура последовательно возвращает (mock_metadata, expected_in, expected_out)"""
    return request.param


@pytest.fixture(
    params=[
        "marketdata_missing_securities.json",
        "securities_empty.json",
        "securities_invalid_types.json",
        "securities_missing_columns.json",
        "securities_missing_marketdata.json",
        {},
        {"securities": None, "marketdata": None},
    ],
    ids=[
        "file_marketdata_missing",
        "file_empty",
        "file_invalid_types",
        "file_missing_columns",
        "file_missing_marketdata",
        "raw_empty_dict",
        "raw_none_structures",
    ],
)
def corrupted_fixture_source(request):
    """Фикстура поочередно отдает каждый невалидный источник данных."""
    return request.param


REFERENCE_DIR = Path(__file__).parents[1] / "data" / "reference"

@pytest.fixture(scope="session")
def reference_market_data() -> pd.DataFrame:
    """
    Эталонный Master-DataFrame для всестороннего тестирования фильтрации и сортировки.
    Динамически загружается из физического CSV-файла в папке data/reference/.
    """
    csv_path = REFERENCE_DIR / "master_market_data.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Критическая ошибка тестов: "
            f"Эталонный файл данных не найден по пути {csv_path}. "
            f"Пожалуйста, создайте папку data/reference/ и "
            f"положите туда master_market_data.csv"
        )
    
    # Читаем CSV. Pandas автоматически превратит пустые ячейки в np.nan (null)
    # keep_default_na=True обеспечивает правильную конвертацию null-значений для ТЗ
    df = pd.read_csv(csv_path, encoding="utf-8")
    
    # Гарантируем сброс индекса к упорядоченному виду 0, 1, 2...
    df.index = range(len(df))
    return df


@pytest.fixture
def initialized_qt_model(reference_market_data):
    """Вспомогательная фикстура: создает Qt-модель и заполняет её эталоном."""
    model = MoexTableModel()
    # Загружаем наш Master-DataFrame в модель таблицы
    model.set_dataframe(reference_market_data)
    return model
