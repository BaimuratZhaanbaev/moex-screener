# src/core/parser.py
from typing import Any

import pandas as pd
from loguru import logger

from src.core.constants import MoexBlocks, MoexColumns
from src.core.extractor import MoexSchemaExtractor


class MoexDataParser:
    def __init__(self, allowed_columns: list[str] = None) -> None:
        self.allowed_columns: list[str] | None = allowed_columns
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
        if not isinstance(raw_data, dict):
            logger.error("Контракт нарушен: сырые данные не являются словарем.")
            return pd.DataFrame()
        
        securities_raw = raw_data.get(MoexBlocks.SECURITIES.value)
        market_raw = raw_data.get(MoexBlocks.MARKETDATA.value)
        
        logger.info("Запуск конвейера трансформации данных MOEX...")

        if not securities_raw or not market_raw:
            logger.warning(
                "Получен пустой или некорректный пакет данных от API. "
                "Возвращаем пустой DataFrame."
            )
            return pd.DataFrame()
        
        try:
            securities_df = self._convert_block_to_df(securities_raw)
            market_df = self._convert_block_to_df(market_raw)
        except Exception as e:
            logger.error(f"Сбой десериализации блоков JSON в DataFrame: {e}")
            return pd.DataFrame()

        if securities_df.empty or market_df.empty:
            return pd.DataFrame()

        try:
            pk = MoexColumns.SECID.value
            
            # Индексация для бесконфликтного выравнивания
            securities_df.set_index(pk, inplace=True, drop=False)
            market_df.set_index(pk, inplace=True, drop=True)

            # Вычисление уникальных колонок котировок (исключая дубликаты индексов)
            unique_market_cols = market_df.columns.difference(securities_df.columns)
            merged_df = securities_df.join(market_df[unique_market_cols], how="left")

            # Извлечение числовых полей через внешний экстрактор (Принцип S из SOLID)
            numeric_cols = MoexSchemaExtractor.extract_numeric_columns(raw_data)
            
            # Фильтрация, кастинг типов и финальная сортировка
            filtered_df = self._filter_columns(merged_df)
            final_df = self._cast_data_types(filtered_df, numeric_cols)

            if pk in final_df.columns:
                final_df.reset_index(drop=True, inplace=True)
                final_df.sort_values(by=pk, inplace=True)

            logger.success(
                f"Конвейер успешно завершен. "
                f"Сформировано записей: {len(final_df)}"
            )
            return final_df
        
        except Exception as e:
            logger.error(
                f"Критическая ошибка в процессе парсинга данных: {e}", exc_info=True
            )
            return pd.DataFrame()

    def _cast_data_types(
        self, df: pd.DataFrame, numeric_columns: list[str],) -> pd.DataFrame:
        """
        Принудительно переводит финансовые метрики в числа
        на основе динамического списка.
        """
        df_casted = df.copy()
        target_cols = df_casted.columns.intersection(numeric_columns)

        for col in target_cols:
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
        
        pk = MoexColumns.SECID.value
        existing_columns = [col for col in self.allowed_columns if col in df.columns]

        # Логируем отсутствие ожидаемых колонок в данных биржи
        missing = set(self.allowed_columns) - set(existing_columns)

        if missing:
            logger.warning(f"В данных отсутствуют запрошенные колонки: {missing}")

        if pk not in existing_columns and pk in df.columns:
            existing_columns.insert(0, pk)
            logger.debug("SECID принудительно добавлен в список отображаемых колонок.")

        logger.info(
            f"Очистка: оставлено {len(existing_columns)} из {len(df.columns)} колонок."
        )
        return df[existing_columns].copy()
