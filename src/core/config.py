# src/core/config.py

# 1. Базовые колонки для быстрого просмотра
DEFAULT_COLUMNS = [
    "SECID", "SHORTNAME", "LAST", "LASTTOPREVPRICE", "VALTODAY_RUR"
]

# 2. Профессиональные колонки (без технического шума)
PROFESSIONAL_COLUMNS = [
    # Идентификаторы
    "SECID", "SHORTNAME", "ISIN", "LISTLEVEL",
    # Масштаб и Объемы
    "ISSUECAPITALIZATION", "VOLTODAY", "VALTODAY_RUR", "NUMTRADES",
    # Ценовые экстремумы
    "OPEN", "HIGH", "LOW", "LAST", "PREVPRICE",
    # Моментум
    "LASTCHANGEPRCNT", "LASTTOPREVPRICE",
    # Микроструктура стакана
    "BID", "OFFER", "SPREAD", "BIDDEPTHT", "OFFERDEPTHT", "NUMBIDS", "NUMOFFERS",
    # Контекст
    "TRADINGSTATUS", "TRADINGSESSION"
]

class UIConfig:
    """Класс для управления настройками видимости и пресетами колонок."""
    def __init__(self):
        self.current_mode = "basic"  # Может быть: basic, professional, full
        self.custom_visible_columns = DEFAULT_COLUMNS.copy()

    def get_columns_to_show(self, all_available_columns: list) -> list:
        """Возвращает список колонок, которые нужно отобразить в интерфейсе."""
        if self.current_mode == "basic":
            return [col for col in DEFAULT_COLUMNS if col in all_available_columns]
        elif self.current_mode == "professional":
            return [col for col in PROFESSIONAL_COLUMNS if col in all_available_columns]
        else:
            # В режиме 'full' показываем пользовательский выбор или вообще всё
            return self.custom_visible_columns if self.custom_visible_columns else all_available_columns
