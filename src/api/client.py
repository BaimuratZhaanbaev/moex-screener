
import json
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

# Эндпоинт из ТЗ
MOEX_ISS_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/securities.json"


class MoexAPIError(Exception):
    """Кастомное исключение для ошибок MOEX ISS API."""

    pass


class MoexClient:
    """Клиент для взаимодействия с API Московской Биржи (MOEX ISS)."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_from_api(self) -> Dict[str, Any]:
        """Выполняет реальный сетевой запрос к Московской Бирже.

        Возвращает сырой словарь (JSON).
        Raises MoexAPIError при любых сетевых проблемах.
        """
        try:
            # Выполняем GET-запрос с ограничением по времени (timeout)
            response = httpx.get(MOEX_ISS_URL, timeout=self.timeout)

            # Проверяем HTTP-статус (вызовет ошибку, если код не 2xx, например 404 или 500)
            response.raise_for_status()

            # Десериализуем JSON
            return response.json()

        except httpx.TimeoutException:
            raise MoexAPIError(
                "Превышено время ожидания ответа от сервера биржи (Timeout)."
            )
        except httpx.HTTPStatusError as e:
            raise MoexAPIError(
                f"Ошибка сервера MOEX. Статус-код: {e.response.status_code}"
            )
        except httpx.RequestError:
            raise MoexAPIError(
                "Сетевая ошибка: проверьте подключение к Интернету."
            )
        except json.JSONDecodeError:
            raise MoexAPIError(
                "Получен некорректный JSON-пакет от сервера MOEX."
            )

    def fetch_from_fixture(self, fixture_name: str) -> Dict[str, Any]:
        """Загружает данные из локальной JSON-фикстуры (для тестов и отладки)."""
        # Ищем папку data/fixtures относительно корня проекта
        fixture_path = (
            Path(__file__).parents[2] / "data" / "fixtures" / fixture_name
        )

        if not fixture_path.exists():
            raise MoexAPIError(f"Файл фикстуры {fixture_name} не найден на диске.")

        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise MoexAPIError(
                f"Критическая ошибка: Файл фикстуры {fixture_name} содержит некорректный JSON."
            )

    def validate_and_parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Проверяет структуру ответа согласно ТЗ (наличие columns и data).

        Если структура верна, возвращает очищенный словарь.
        """
        # Проверяем базовое присутствие корневого блока
        if "securities" not in raw_data:
            raise MoexAPIError(
                "Неверная структура ответа API: отсутствует блок 'securities'."
            )

        securities = raw_data["securities"]

        # Жесткое требование ТЗ: проверка колонок и данных перед конвертацией в DataFrame
        if "columns" not in securities or "data" not in securities:
            raise MoexAPIError(
                "Ошибка валидации: в структуре 'securities' нет полей 'columns' или 'data'."
            )

        # Опционально: если мы решили использовать расширенный вариант с marketdata
        if "marketdata" in raw_data:
            marketdata = raw_data["marketdata"]
            if "columns" not in marketdata or "data" not in marketdata:
                raise MoexAPIError(
                    "Ошибка валидации: в структуре 'marketdata' нарушен формат колонок/данных."
                )

        return raw_data
