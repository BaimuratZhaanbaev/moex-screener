import time

import pandas as pd
from loguru import logger


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

        working_df = df  # Работаем по ссылке, память не дублируем

        # Текстовые фильтры (регистронезависимые)
        if ticker:
            working_df = working_df[
                working_df["SECID"].str.contains(ticker, case=False, na=False)
            ]

        if name:
            working_df = working_df[
                working_df["SHORTNAME"].str.contains(name, case=False, na=False)
            ]

        # Числовые фильтры цены (LAST)
        if price_from is not None:
            working_df = working_df[
                (working_df["LAST"].notna()) & (working_df["LAST"] >= price_from)
            ]

        if price_to is not None:
            working_df = working_df[
                (working_df["LAST"].notna()) & (working_df["LAST"] <= price_to)
            ]

        # Числовые фильтры изменения цены (LASTTOPREVPRICE)
        if change_from is not None:
            working_df = working_df[
                working_df["LASTTOPREVPRICE"].notna()
                & (working_df["LASTTOPREVPRICE"] >= change_from)
            ]

        if change_to is not None:
            working_df = working_df[
                working_df["LASTTOPREVPRICE"].notna()
                & (working_df["LASTTOPREVPRICE"] <= change_to)
            ]

        # Замеряем итоговые метрики
        elapsed_time = (time.perf_counter() - start_time) * 1000  # переводим в мс
        final_rows = len(working_df)

        logger.success(
            f"Фильтрация завершена за {elapsed_time:.2f} мс. "
            f"Было строк: {initial_rows} -> Осталось: "
            f"{final_rows} (Отсечено: {initial_rows - final_rows})"
        )

        return working_df
