# src/core/parser.py
from typing import Any

import pandas as pd
from loguru import logger


class MoexDataParser:
    def __init__(self, allowed_columns: list[str] = None):
        self.allowed_columns = allowed_columns
        logger.debug(
            "Инициализирован MoexDataParser с динамическим определением типов."
        )

    def parse_to_dataframe(self, raw_data: dict[str, Any]) -> pd.DataFrame:
        """
        Главный фасадный метод конвейера трансформации данных.
        Принимает грязный JSON-словарь, возвращает чистый отсортированный DataFrame.

        :param raw_data: Десериализованный JSON-ответ от MOEX ISS API.
        :return: Очищенный pd.DataFrame, готовый к фильтрации и выводу в Qt.
        """
        logger.info("Запуск конвейера трансформации данных MOEX...")

        if not raw_data or "securities" not in raw_data or "marketdata" not in raw_data:
            logger.warning(
                "Получен пустой или некорректный пакет данных от API. "
                "Возвращаем пустой DataFrame."
            )
            return pd.DataFrame()

        try:
            # 1. Автоматически извлекаем числовые колонки на основе метаданных ответа!
            numeric_cols = self._get_numeric_columns(raw_data)
            logger.debug(f"Идентификация числовых колонок биржи: {numeric_cols}")

            # 2. Конвертируем блоки
            logger.debug("Десериализация блока 'securities'...")
            sec_df = self._convert_block_to_df(raw_data["securities"])
            logger.debug("Десериализация блока 'marketdata'...")
            market_df = self._convert_block_to_df(raw_data["marketdata"])

            if sec_df.empty or market_df.empty:
                logger.warning("Один из ключевых информационных блоков пуст.")
                return pd.DataFrame()

            # 3. Реляционное слияние таблиц (Left Join) по первичному ключу SECID
            logger.debug("Выполнение реляционного слияния таблиц по ключу SECID...")
            merged_df = pd.merge(sec_df, market_df, on="SECID", how="left")
            logger.info(
                f"Реляционное слияние успешно завершено. "
                f"Сформировано записей: {len(merged_df)}"
            )

            # Лог аномалии слияния
            if len(merged_df) < len(sec_df):
                logger.error(
                    "Размер таблицы уменьшился после слияния! "
                    "Возможно, нарушена уникальность SECID."
                )

            # Очистка от инфраструктурного шума (фильтрация колонок)
            cleaned_df = self._filter_columns(merged_df)

            # 4. Приведение типов с использованием динамического списка
            final_df = self._cast_data_types(cleaned_df, numeric_cols)
            return final_df
        except Exception as e:
            logger.error(
                f"Критическая ошибка в процессе парсинга данных: {e}", exc_info=True
            )
            return pd.DataFrame()

    def _get_numeric_columns(self, raw_data: dict[str, Any]) -> list[str]:
        """
        Автоматически извлекает названия колонок числовых типов из метаданных MOEX ISS.
        """
        numeric_fields = []

        # Проверяем метаданные в обоих информационных блоках
        for block_name in ["securities", "marketdata"]:
            block = raw_data.get(block_name, {})
            metadata = block.get("metadata", {})

            if not metadata:
                logger.warning(f"Метаданные для блока '{block_name}' не найдены.")
                continue

            for col_name, info in metadata.items():
                data_type = info.get("type", "").lower()

                # Если тип равен double, float, int32 или int64 — это число
                if "double" in data_type or "int" in data_type or "float" in data_type:
                    if col_name not in numeric_fields:
                        numeric_fields.append(col_name)

            logger.debug(
                f"В блоке '{block_name}' обнаружено {len(numeric_fields)} "
                "числовых полей."
            )

        logger.info(
            f"Парсер определил {len(numeric_fields)} числовых колонок для обработки."
        )
        return numeric_fields

    def _cast_data_types(
        self, df: pd.DataFrame, numeric_columns: list[str]
    ) -> pd.DataFrame:
        """
        Принудительно переводит финансовые метрики в числа
        на основе динамического списка.
        """
        df_casted = df.copy()

        for col in df_casted.columns:
            if col in numeric_columns:
                # Наше требование ТЗ: null -> NaN (не ноль!)
                df_casted[col] = pd.to_numeric(df_casted[col], errors="coerce")

        logger.debug(
            "Приведение типов данных завершено. Значения null изолированы как NaN."
        )
        return df_casted

    def _convert_block_to_df(self, block: dict[str, Any]) -> pd.DataFrame:
        """
        Внутренний метод преобразования специфической структуры MOEX (columns/data)
        в DataFrame.
        """
        columns = block.get("columns")
        data = block.get("data")

        if not columns or not data:
            logger.warning(
                "Попытка обработки пустого блока данных (columns или data отсутствуют)."
            )
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=columns)
        logger.debug(
            f"Блок успешно десериализован: {df.shape[0]} строк, {df.shape[1]} колонок."
        )
        return df

    def _filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Оставляет в датафрейме только целевые колонки без технического шума"""
        if not self.allowed_columns:
            logger.debug(
                "Список allowed_columns не задан, возвращаем исходный DataFrame."
            )
            return df

        existing_columns = [col for col in self.allowed_columns if col in df.columns]

        # Логируем отсутствие ожидаемых колонок в данных биржи
        missing = set(self.allowed_columns) - set(existing_columns)

        if missing:
            logger.warning(f"В данных отсутствуют запрошенные колонки: {missing}")

        if "SECID" not in existing_columns and "SECID" in df.columns:
            existing_columns.insert(0, "SECID")
            logger.debug("SECID принудительно добавлен в список отображаемых колонок.")

        logger.info(
            f"Очистка: оставлено {len(existing_columns)} из {len(df.columns)} колонок."
        )
        return df[existing_columns].copy()
