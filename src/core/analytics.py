import time

import pandas as pd
from loguru import logger

from src.core.constants import MoexColumns


class DataFilterService:
    """Сервис чистого анализа и фильтрации данных (Бизнес-логика)."""

    @staticmethod
    def filter_market_data(
        df: pd.DataFrame,
        ticker: str = "",
        name: str = "",
        price_from: float | None = None,
        price_to: float | None = None,
        change_from: float | None = None,
        change_to: float | None = None,
    ) -> pd.DataFrame:
        """Применяет маски к DataFrame и возвращает новый отфильтрованный срез."""
        if df.empty:
            logger.warning("Фильтрация отменена: передан пустой DataFrame.")
            return df

        initial_rows = len(df)
        start_time = time.perf_counter()  # Фиксируем время старта

        # Подгружаем строгие ключи колонок из наших констант
        col_secid = MoexColumns.SECID.value
        col_name = MoexColumns.SHORTNAME.value
        col_last = MoexColumns.LAST.value
        col_change = MoexColumns.LASTTOPREVPRICE.value

        # Собираем активные фильтры для лога
        active_filters = []
        if ticker:
            active_filters.append(f"ticker='{ticker}'")
        if name:
            active_filters.append(f"name='{name}'")
        if price_from is not None or price_to is not None:
            active_filters.append(f"price=[{price_from}:{price_to}]")
        if change_from is not None or change_to is not None:
            active_filters.append(f"change=[{change_from}:{change_to}]")
        logger.info(
            f"Запуск фильтрации. Активные критерии: "
            f"{', '.join(active_filters) if active_filters else 'НЕТ'}"
        )

        # Текстовые фильтры (регистронезависимые). Накладываем битовые фильтры на маску
        mask = pd.Series(True, index=df.index)
        
        if ticker:
            mask &= df[col_secid].str.contains(ticker, case=False, na=False)

        if name:
            mask &= df[col_name].str.contains(name, case=False, na=False)

        # Числовые фильтры цены (LAST)
        if price_from is not None:
            mask &= df[col_last].notna() & (df[col_last] >= price_from)

        if price_to is not None:
            mask &= df[col_last].notna() & (df[col_last] <= price_to)

        # Числовые фильтры изменения цены (LASTTOPREVPRICE)
        if change_from is not None:
            mask &= df[col_change].notna() & (df[col_change] >= change_from)

        if change_to is not None:
            mask &= df[col_change].notna() & (df[col_change] <= change_to)

        # Выделяем память под срез данных ровно ОДИН раз
        filtered_df = df[mask].copy()

        # Замеряем итоговые метрики
        elapsed_time = (time.perf_counter() - start_time) * 1000  # переводим в мс

        logger.success(
            f"Фильтрация завершена за {elapsed_time:.2f} мс. "
            f"Было строк: {len(df)} -> Осталось: {len(filtered_df)}"
        )

        return filtered_df
