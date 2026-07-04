# src/core/config.py

# 1. Базовые колонки для быстрого просмотра
DEFAULT_COLUMNS = ["SECID", "SHORTNAME", "LAST", "LASTTOPREVPRICE", "VALTODAY_RUR"]

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
    "TRADINGSTATUS", "TRADINGSESSION",
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
            return (
                self.custom_visible_columns
                if self.custom_visible_columns
                else all_available_columns
            )

# Человекочитаемые заголовки для GUI
COLUMN_MAPPING = {
    "SECID": "Тикер",
    "SHORTNAME": "Наименование",
    "ISIN": "ISIN",
    "LISTLEVEL": "Эшелон",
    "ISSUECAPITALIZATION": "Капитализация",
    "VOLTODAY": "Объем (шт.)",
    "VALTODAY_RUR": "Оборот (руб.)",
    "NUMTRADES": "Кол-во сделок",
    "OPEN": "Открытие",
    "HIGH": "Максимум",
    "LOW": "Минимум",
    "LAST": "Цена последней",
    "PREVPRICE": "Вчерашнее закр.",
    "LASTTOPREVPRICE": "Изм. (%)",
    "BID": "Лучший спрос (BID)",
    "OFFER": "Лучшее предл. (OFFER)",
    "SPREAD": "Спред",
    "WAPRICE": "Средневзв. цена (VWAP)",
    # ... сюда добавляем все остальные нужные колонки из ТЗ ...
}

# Группы форматирования финансовых данных
FORMAT_GROUPS = {
    "price_2dp": [ # Дробные цены с 2 знаками и пробелом
        "LAST", "OPEN", "HIGH", "LOW", "PREVPRICE", 
        "BID", "OFFER", "HIGHBID", "LOWOFFER", "WAPRICE", "PREVWAPRICE"
    ], 
    "percent": [ # Проценты со знаком +/-
        "LASTCHANGEPRCNT", "LASTTOPREVPRICE", "WAPTOPREVWAPRICEPRCNT"
        ],
    "integer_volume": [ # Целые штуки
        "VOLTODAY", "NUMTRADES", "BIDDEPTH", "OFFERDEPTH", "NUMBIDS", "NUMOFFERS"
        ], 
    "large_money": [ # Огромные суммы без копеек
        "VALTODAY_RUR", "ISSUECAPITALIZATION"
        ], 
}
