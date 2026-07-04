# src/core/analytics.py
import pandas as pd
from typing import Optional
from loguru import logger

class DataFilterService:
    """Сервис чистого анализа и фильтрации данных (Бизнес-логика)."""
    
    @staticmethod
    def filter_market_data(
        df: pd.DataFrame,
        ticker: str = "",
        name: str = "",
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        change_from: Optional[float] = None,
        change_to: Optional[float] = None,
    ) -> pd.DataFrame:
        """Применяет маски к DataFrame и возвращает новый отфильтрованный срез."""
        if df.empty:
            return df
            
        working_df = df # Работаем по ссылке, память не дублируем

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

        logger.debug(f"Фильтрация завершена. ")
        return working_df
    