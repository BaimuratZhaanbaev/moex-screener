"""Модуль парсинга и структурной трансформации данных Московской Биржи.

Отвечает за сборку, реляционное объединение (Left Join) таблиц инструментов и
котировок MOEX ISS API, а также обеспечивает динамическую строгую типизацию
и защиту от конфликтов многоуровневых индексов Pandas.
"""

from typing import Any

import pandas as pd
from loguru import logger

from src.core.constants import MoexBlocks, MoexColumns
from src.core.extractor import MoexSchemaExtractor


class MoexDataParser:
    """Парсер сырых данных MOEX ISS API, управляющий конвейером трансформации."""

    def __init__(self, allowed_columns: list[str] | None = None) -> None:
        """Инициализирует конвейер парсинга с опциональной конфигурацией пресета.

        Args:
            allowed_columns (list[str] | None, optional): Список колонок, которые
                необходимо сохранить. Если равен None — сохраняются все поля.
        """
        self.allowed_columns: list[str] | None = allowed_columns
        logger.debug(
            "Инициализирован MoexDataParser с динамическим определением типов."
        )

    def parse_to_dataframe(self, raw_data: dict[str, Any]) -> pd.DataFrame:
        """Реализует сквозную сборку, очистку и реляционное слияние таблиц MOEX.

        Последовательно проверяет входные контракты, производит
        атомарную десериализацию блоков, связывает статический справочник
        и динамический стакан по ключу SECID, после чего сбрасывает неоднозначные
        индексы Pandas перед финальной сортировкой.

        Args:
            raw_data (dict[str, Any]): Сырой JSON-пакет от ответа ISS API Мосбиржи.

        Returns:
            pd.DataFrame: Очищенная, отсортированная по тикеру и строго типизированная
                матрица данных, готовая для передачи в слой аналитики и Qt Model.
        """
        # 1. Ограничивающие условия (принцип быстрого отказа)
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
        
        # 2. Изолированная десериализация блоков JSON в DataFrames
        try:
            securities_df = self._convert_block_to_df(securities_raw)
            market_df = self._convert_block_to_df(market_raw)
        except Exception as e:
            logger.error(f"Сбой десериализации блоков JSON в DataFrame: {e}")
            return pd.DataFrame()

        if securities_df.empty or market_df.empty:
            return pd.DataFrame()

        # 3. Выравнивание, реляционное объединение и нормализация
        try:
            pk = MoexColumns.SECID.value
            
            # Временная индексация для корректного горизонтального слияния по тикеру
            securities_df.set_index(pk, inplace=True, drop=False)
            market_df.set_index(pk, inplace=True, drop=True)

            # Вычисление уникального среза колонок котировок для предотвращения коллизий
            unique_market_cols = market_df.columns.difference(securities_df.columns)
            merged_df = securities_df.join(market_df[unique_market_cols], how="left")

            # Анализ типов метаданных внешней службой
            numeric_cols = MoexSchemaExtractor.extract_numeric_columns(raw_data)
            
            # Фильтрация структуры и приведение типов финансовых метрик
            filtered_df = self._filter_columns(merged_df)
            final_df = self._cast_data_types(filtered_df, numeric_cols)

            # Устранение неоднозначности 'SECID' (как индекс и как колонка одновременно)
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
        self, 
        df: pd.DataFrame, 
        numeric_columns: list[str],
    ) -> pd.DataFrame:
        """Типизирует финансовые метрики в числа с изоляцией пустых значений.

        Переводит задекларированные числовые столбцы в float/int. В соответствии с ТЗ,
        ошибочные или пустые финансовые ячейки (null) переводит в NaN (а не в ноль).

        Args:
            df (pd.DataFrame): Объединенный нетипизированный DataFrame.
            numeric_columns (set[str]): Справочный набор числовых колонок от экстрактора.

        Returns:
            pd.DataFrame: Копия DataFrame с нормализованными типами данных.
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
        """Преобразует внутренний табличный узел ответа MOEX (columns/data) в DataFrame.

        Args:
            block (dict[str, Any]): Конкретный информационный узел JSON-пакета биржи.

        Returns:
            pd.DataFrame: 
                Плоская таблица данных Pandas или пустой DataFrame в случае неудачи.
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
        """Очищает итоговый датафрейм от избыточных колонок и технического шума.

        Args:
            df (pd.DataFrame): Исходная объединенная матрица данных.

        Returns:
            pd.DataFrame: Срез данных, содержащий только целевые колонки текущего пресета.
        """
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

        # Обязательное наличие ключевого тикера на первой позиции таблицы
        if pk not in existing_columns and pk in df.columns:
            existing_columns.insert(0, pk)
            logger.debug("SECID принудительно добавлен в список отображаемых колонок.")

        logger.info(
            f"Очистка: оставлено {len(existing_columns)} из {len(df.columns)} колонок."
        )
        return df[existing_columns].copy()
