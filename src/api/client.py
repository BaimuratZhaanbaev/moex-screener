import json
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

# Эндпоинт MOEX_ISS
MOEX_ISS_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/securities.json"


class MoexAPIError(Exception):
    """Кастомное исключение для ошибок MOEX ISS API."""

    pass


class MoexClient:
    """Клиент для взаимодействия с API Московской Биржи (MOEX ISS)."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_from_api(self) -> dict[str, Any]:
        """
        Выполняет реальный сетевой запрос к Московской Бирже.
        Возвращает сырой словарь (JSON).
        Raises MoexAPIError при любых сетевых проблемах.
        """
        logger.info(f"Запрос данных к MOEX ISS (таймаут: {self.timeout}с)...")

        try:
            # Выполняем GET-запрос с ограничением по времени (timeout)
            response = httpx.get(MOEX_ISS_URL, timeout=self.timeout)
            logger.debug(
                f"Ответ сервера: {response.status_code} "
                f"размер: {len(response.content)} байт"
            )
            # Проверяем HTTP-статус 
            # (вызовет ошибку, если код не 2xx, например 404 или 500)
            response.raise_for_status()

            # Десериализуем JSON
            data = response.json()
            logger.debug("Данные успешно получены с сервера.")
            return data
        except httpx.TimeoutException:
            logger.error("Ошибка: Превышено время ожидания ответа от сервера.")
            raise MoexAPIError(
                "Превышено время ожидания ответа от сервера биржи (Timeout)."
                )        
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка HTTP {e.response.status_code}: {e.response.text}")
            raise MoexAPIError(
                f"Ошибка сервера MOEX. Статус-код: {e.response.status_code}"
            )        
        except httpx.RequestError:
            logger.exception("Сетевая ошибка при запросе к MOEX.")
            raise MoexAPIError("Сетевая ошибка: проверьте подключение к Интернету.")
        except json.JSONDecodeError:
            logger.error("Ошибка: Получен некорректный JSON-пакет.")
            raise MoexAPIError("Получен некорректный JSON-пакет от сервера MOEX.")
        except Exception as e:
            # Ловим вообще любую ошибку, которую не предвидели
            logger.exception(f"Непредвиденная ошибка: {e}")
            raise MoexAPIError(
                f"Произошла непредвиденная ошибка: {type(e).__name__}: {e}"
            )

    def fetch_from_fixture(self, fixture_name: str) -> dict[str, Any]:
        """Загружает данные из локальной JSON-фикстуры (для тестов и отладки)."""
        # Ищем папку data/fixtures относительно корня проекта
        fixture_path = Path(__file__).parents[2] / "data" / "fixtures" / fixture_name
        logger.info(f"Процесс загрузки данных из фикстуры: {fixture_name}")

        if not fixture_path.exists():
            logger.error(f"Файл фикстуры не найден: {fixture_path} не найден на диске.")
            raise MoexAPIError(f"Файл фикстуры {fixture_name} не найден на диске.")

        try:
            with open(fixture_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.exception(
                f"Ошибка парсинга JSON в файле {fixture_name}, "
                 "содержит некорректный JSON"
            )
            raise MoexAPIError(
                f"Критическая ошибка: Файл фикстуры {fixture_name} "
                "содержит некорректный JSON."
            )

    def validate_and_parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Проверяет структуру ответа согласно ТЗ (наличие columns и data).
        Если структура верна, возвращает очищенный словарь.
        """
        logger.debug("Валидация структуры ответа...")

        # Проверяем базовое присутствие корневого блока
        if "securities" not in raw_data:
            logger.error("Валидация провалена: блок 'securities' отсутствует.")
            raise MoexAPIError(
                "Неверная структура ответа API: отсутствует блок 'securities'."
            )
        
        # Проверяем базовое присутствие корневого блока marketdata
        if "marketdata" not in raw_data:
            logger.error("Валидация провалена: блок 'marketdata' отсутствует.")
            raise MoexAPIError(
                "Неверная структура ответа API: отсутствует блок 'marketdata'."
            )

        securities = raw_data["securities"]
        marketdata = raw_data["marketdata"]

        # Требование ТЗ: проверка колонок и данных перед конвертацией в DataFrame
        if "columns" not in securities or "data" not in securities:
            logger.error("Валидация провалена: поля 'columns' или 'data' отсутствуют.")
            raise MoexAPIError(
                "Ошибка валидации: "
                "в структуре 'securities' нет полей 'columns' или 'data'."
            )
        
        # Точно так же строго проверяем внутренности блока 'marketdata'
        if "columns" not in marketdata or "data" not in marketdata:
            logger.error("Валидация провалена: в 'marketdata' отсутствуют 'columns' или 'data'.")
            raise MoexAPIError(
                "Ошибка валидации: в структуре 'marketdata' нет полей 'columns' или 'data'."
            )

        logger.info("Валидация данных прошла успешно.")
        return raw_data

    def get_clean_data(self, use_fixture: str | None = None) -> dict[str, Any]:
        """
        Универсальный конвейер (фасадный метод).
        Скачивает (или берет из фикстуры) данные и прогоняет через валидацию структуры.
        Именно его мы будем вызывать из фонового потока Qt.
        """
        # Логируем начало процесса
        if use_fixture:
            logger.info(
                f"Запуск конвейера данных: берем локальную фикстуру '{use_fixture}'"
            )
            raw_data = self.fetch_from_fixture(use_fixture)
        else:
            logger.info(
                "Запуск конвейера данных: отправка сетевого запроса к MOEX ISS API"
            )
            raw_data = self.fetch_from_api()

        # Логируем переход к валидации
        logger.debug("Сырые данные получены. Начинаем валидацию и парсинг структуры...")

        try:
            cleaned_data = self.validate_and_parse(raw_data)
            logger.success(
                "Конвейер успешно завершен. Данные валидны и готовы к отображению."
            )
            return cleaned_data
        except Exception as e:
            # Ловим ошибки валидации, чтобы поток не упал молча
            logger.error(f"Конвейер остановлен из-за ошибки валидации: {e}")
            raise
