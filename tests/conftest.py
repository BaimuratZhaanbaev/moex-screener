import json
from pathlib import Path
import pytest

# Базовый путь к фикстурам
FIXTURES_DIR = Path(__file__).parents[1] / "data" / "fixtures"

@pytest.fixture
def load_fixture():
    """Фабрика-фикстура для динамической загрузки любого JSON по имени файла."""
    def _load(filename: str) -> dict:
        file_path = FIXTURES_DIR / filename
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    return _load

@pytest.fixture
def real_api_data(load_fixture):
    """Фикстура, отдающая готовый словарь из securities_real.json."""
    return load_fixture("securities_real.json")