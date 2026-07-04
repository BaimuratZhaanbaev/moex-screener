# src/core/constants.py

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
    # ... сюда добавляем все остальные нужные колонки ...
}

# Группы форматирования финансовых данных для Qt-модели
FORMAT_GROUPS = {
    "price_2dp": [
        "LAST", "OPEN", "HIGH", "LOW", "PREVPRICE", "BID", "OFFER", "WAPRICE"
    ],
    "percent": [
        "LASTTOPREVPRICE", "LASTCHANGEPRCNT", "SPREAD"
    ],
    "money_int": [
        "VALTODAY_RUR", "ISSUECAPITALIZATION"
    ],
    "volume_int": [
        "VOLTODAY", "NUMTRADES", "NUMBIDS", "NUMOFFERS"
    ]
}

# Группы форматирования финансовых данных
FORMAT_GROUPS = {
    "price_2dp": [  # Дробные цены с 2 знаками и пробелом
        "LAST",
        "OPEN",
        "HIGH",
        "LOW",
        "PREVPRICE",
        "BID",
        "OFFER",
        "HIGHBID",
        "LOWOFFER",
        "WAPRICE",
        "PREVWAPRICE",
    ],
    "percent": [  # Проценты со знаком +/-
        "LASTCHANGEPRCNT",
        "LASTTOPREVPRICE",
        "WAPTOPREVWAPRICEPRCNT",
    ],
    "integer_volume": [  # Целые штуки
        "VOLTODAY",
        "NUMTRADES",
        "BIDDEPTH",
        "OFFERDEPTH",
        "NUMBIDS",
        "NUMOFFERS",
    ],
    "large_money": [  # Огромные суммы без копеек
        "VALTODAY_RUR",
        "ISSUECAPITALIZATION",
    ],
}