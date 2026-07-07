"""Модуль сетевого взаимодействия с программным интерфейсом Московской Биржи.

Обеспечивает отправку HTTP-запросов к MOEX ISS API, загрузку локальных
тестовых фикстур, а также первичную валидацию структуры входящих пакетов данных.
"""

import json
from pathlib import Path
from typing import Any, Final

import httpx
from loguru import logger

# Информационный адрес эндпоинта Московской Биржи (Рынок акций, режим Т+)
MOEX_ISS_URL: Final[str] = (
    "https://iss.moex.com/iss/engines/stock/markets/shares/securities.json"
)


class MoexAPIError(Exception):
    """Кастомное исключение для сбоев транспортного и валидационного уровней."""

    pass


class MoexClient:
    """Транспортный клиент для работы со спецификацией MOEX ISS API."""

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        """Инициализирует сетевой клиент с заданными параметрами сессии.

        Args:
            timeout (float, optional): Предельное время ожидания ответа
                от серверов биржи в секундах. По умолчанию 10.0.
        """
        self.timeout: float = timeout

    def fetch_from_api(self) -> dict[str, Any]:
        """ "Выполняет синхронный GET-запрос к API Московской Биржи.

        Запрашивает актуальный снимок котировок торговой сессии. Автоматически
        обрабатывает сетевые аномалии и переводит их в формат внутренних исключений.

        Returns:
            dict[str, Any]: Десериализованный JSON-ответ от сервера в виде словаря.

        Raises:
            MoexAPIError: Если превышен таймаут, получен некорректный статус-код
                (4xx/5xx), отсутствует интернет-соединение или пакет поврежден.
        """
        logger.info(f"Запрос данных к MOEX ISS (таймаут: {self.timeout}с)...")

        try:
            response = httpx.get(MOEX_ISS_URL, timeout=self.timeout)
            logger.debug(
                f"Ответ сервера: {response.status_code} "
                f"размер: {len(response.content)} байт"
            )
            # Генерация исключения при HTTP-статусах ошибок (4xx, 5xx)
            response.raise_for_status()

            data: dict[str, Any] = response.json()
            logger.debug("Данные успешно получены с сервера и десериализованы..")
            return data

        except httpx.TimeoutException as e:
            logger.error("Превышено время ожидания ответа от серверов MOEX ISS.")
            raise MoexAPIError(
                "Превышено время ожидания ответа от сервера биржи (Timeout)."
            ) from e

        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка HTTP {e.response.status_code}: {e.response.text}")
            raise MoexAPIError(
                f"Произошла непредвиденная ошибка: {type(e).__name__}: {e}"
            ) from e

        except httpx.RequestError as e:
            logger.exception("Сетевая ошибка транспортного уровня при запросе к MOEX.")
            raise MoexAPIError(
                "Сетевая ошибка: проверьте подключение к Интернету."
            ) from e

        except json.JSONDecodeError as e:
            logger.error("Получен необрабатываемый или поврежденный JSON-пакет.")
            raise MoexAPIError(
                "Получен некорректный JSON-пакет от сервера MOEX."
            ) from e

        except Exception as e:
            logger.exception(f"Непредвиденная системная ошибка: {e}")
            raise MoexAPIError(
                f"Произошла непредвиденная ошибка: {type(e).__name__}: {e}"
            ) from e

    def fetch_from_fixture(self, fixture_name: str) -> dict[str, Any]:
        """Загружает снимок рынка из локального статического файла фикстуры.

        Используется в изолированных тестовых сценариях и для имитации работы
        сервера при автономной разработке.

        Args:
            fixture_name (str): Имя целевого JSON-файла фикстуры.

        Returns:
            dict[str, Any]: Структурированный словарь рыночных данных.

        Raises:
            MoexAPIError: Если целевой файл физически отсутствует на диске
                или содержит синтаксические ошибки JSON.
        """
        # Определение абсолютного пути к директории фикстур относительно пакета
        fixture_path = Path(__file__).parents[2] / "data" / "fixtures" / fixture_name
        logger.info(f"Процесс загрузки данных из фикстуры: {fixture_name}")

        if not fixture_path.exists():
            logger.error(f"Файл фикстуры не обнаружен: {fixture_path}")
            raise MoexAPIError(f"Файл фикстуры {fixture_name} не найден на диске.")

        try:
            with open(fixture_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except json.JSONDecodeError as e:
            logger.exception(f"Файл {fixture_name} содержит синтаксические ошибки.")
            raise MoexAPIError(
                f"Критическая ошибка: Файл фикстуры {fixture_name} "
                "содержит некорректный JSON.",
            ) from e

    def validate_and_parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Осуществляет структурную валидацию полученного ответа согласно ТЗ.

        Проверяет наличие обязательных корневых объектов ('securities', 'marketdata'),
        а также вложенных списков описания метаданных ('columns') и кортежей ('data').

        Args:
            raw_data (dict[str, Any]): Непроверенный словарь сырых данных.

        Returns:
            dict[str, Any]: Валидированный словарь, пригодный для передачи парсеру.

        Raises:
            MoexAPIError: При обнаружении структурных несоответствий или
                отсутствии целевых полей.
        """
        logger.debug("Валидация внутренней архитектуры ответа биржи...")

        # Проверка верхнего уровня: спецификации инструментов
        if "securities" not in raw_data:
            logger.error("Валидация провалена: корневой блок 'securities' отсутствует.")
            raise MoexAPIError(
                "Неверная структура ответа API: отсутствует блок 'securities'."
            )

        # Проверка верхнего уровня: спецификации рыночных параметров (стаканы, сделки)
        if "marketdata" not in raw_data:
            logger.error("Валидация провалена: корневой блок 'marketdata' отсутствует.")
            raise MoexAPIError(
                "Неверная структура ответа API: отсутствует блок 'marketdata'."
            )

        securities = raw_data["securities"]
        marketdata = raw_data["marketdata"]

        # Проверка табличной целостности блока инструментов
        if "columns" not in securities or "data" not in securities:
            logger.error(
                "Валидация провалена: в 'securities' отсутствуют 'columns' или 'data'."
            )
            raise MoexAPIError(
                "Ошибка валидации: "
                "в структуре 'securities' нет полей 'columns' или 'data'."
            )

        # Проверка табличной целостности блока рыночных параметров
        if "columns" not in marketdata or "data" not in marketdata:
            logger.error(
                "Валидация провалена: в 'marketdata' отсутствуют 'columns' или 'data'."
            )
            raise MoexAPIError(
                "Ошибка валидации: "
                "в структуре 'marketdata' нет полей 'columns' или 'data'."
            )

        logger.info("Валидация структуры ответа успешно пройдена.")
        return raw_data

    def get_clean_data(self, use_fixture: str | None = None) -> dict[str, Any]:
        """Фасадный метод конвейера поставки данных (Data Pipeline).

        Реализует сквозной процесс: выбор источника (сеть или диск), извлечение
        данных и их последующую строгую верификацию. Рекомендуется для вызова
        в изолированных фоновых рабочих потоках Qt.

        Args:
            use_fixture (str | None, optional): Имя фикстуры, если требуется
                переключить конвейер в офлайн-режим отладки. По умолчанию None.

        Returns:
            dict[str, Any]: Полностью проверенный и валидный словарь данных.

        Raises:
            MoexAPIError: При сбое на любом этапе выполнения конвейера.
        """
        if use_fixture:
            logger.info(
                f"Запуск конвейера данных: чтение локального файла '{use_fixture}'"
            )
            raw_data = self.fetch_from_fixture(use_fixture)
        else:
            logger.info(
                "Запуск конвейера данных: отправка запроса к серверам MOEX ISS API"
            )
            raw_data = self.fetch_from_api()

        logger.debug("Сырые данные получены. Переход к этапу верификации...")

        try:
            cleaned_data = self.validate_and_parse(raw_data)
            logger.success(
                "Работа конвейера успешно завершена. Срез данных готов к трансформации."
            )
            return cleaned_data
        except Exception as e:
            logger.error(f"Конвейер аварийно остановлен на этапе валидации: {e}")
            raise
