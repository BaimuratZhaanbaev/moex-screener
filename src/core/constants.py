"""Глобальные константы и справочники Скринера Московской Биржи.

Содержит конфигурации пресетов колонок, правила локализации заголовков
и группы форматирования финансовых данных для слоя отображения (View).
"""

# Пресет 1. Базовые колонки для экспресс-анализа (Минимальный трафик)
DEFAULT_COLUMNS: list[str] = [
    "SECID",
    "SHORTNAME",
    "LAST",
    "LASTTOPREVPRICE",
    "VALTODAY_RUR",
]

# Пресет 2. Профессиональные метрики (Анализ ликвидности и микроструктуры стакана)
PROFESSIONAL_COLUMNS: list[str] = [
    # Идентификаторы бумаги
    "SECID",
    "SHORTNAME",
    "ISIN",
    "LISTLEVEL",
    # Объемы торгов и масштабы эмитента
    "ISSUECAPITALIZATION",
    "VOLTODAY",
    "VALTODAY_RUR",
    "NUMTRADES",
    # Ценовые экстремумы текущей сессии
    "OPEN",
    "HIGH",
    "LOW",
    "LAST",
    "PREVPRICE",
    # Скорость и изменение (Моментум)
    "LASTCHANGEPRCNT",
    "LASTTOPREVPRICE",
    # Параметры ликвидности (Очередь заявок)
    "BID",
    "OFFER",
    "SPREAD",
    "BIDDEPTHT",
    "OFFERDEPTHT",
    "NUMBIDS",
    "NUMOFFERS",
    # Системные флаги торговой сессии
    "TRADINGSTATUS",
    "TRADINGSESSION",
]

# Справочник локализации системных полей MOEX ISS API для шапки таблицы GUI
COLUMN_MAPPING: dict[str, str] = {
    "SECID": "Тикер",
    "SHORTNAME": "Наименование",
    "ISIN": "Международный код (ISIN)",
    "LISTLEVEL": "Уровень листинга",
    "ISSUECAPITALIZATION": "Рыночная капитализация",
    "VOLTODAY": "Объем торгов (шт.)",
    "VALTODAY_RUR": "Оборот торгов (руб.)",
    "NUMTRADES": "Количество сделок",
    "OPEN": "Цена открытия",
    "HIGH": "Дневной максимум",
    "LOW": "Дневной минимум",
    "LAST": "Цена последней сделки",
    "PREVPRICE": "Цена закрытия вчера",
    "LASTTOPREVPRICE": "Изменение к закрытию (%)",
    "LASTCHANGEPRCNT": "Изменение к открытию (%)",
    "BID": "Лучший спрос (BID)",
    "OFFER": "Лучшее предложение (OFFER)",
    "SPREAD": "Абсолютный спред",
    "WAPRICE": "Средневзвешенная цена (VWAP)",
    "BIDDEPTHT": "Суммарный спрос в стакане",
    "OFFERDEPTHT": "Суммарное предложение в стакане",
    "NUMBIDS": "Заявок на покупку",
    "NUMOFFERS": "Заявок на продажу",
    "TRADINGSTATUS": "Статус торгов",
    "TRADINGSESSION": "Тип сессии",
}

# Группы форматирования финансовых данных для Qt-модели
FORMAT_GROUPS = {
    "price_2dp": [
        "LAST",
        "OPEN",
        "HIGH",
        "LOW",
        "PREVPRICE",
        "BID",
        "OFFER",
        "WAPRICE",
    ],
    "percent": ["LASTTOPREVPRICE", "LASTCHANGEPRCNT", "SPREAD"],
    "money_int": ["VALTODAY_RUR", "ISSUECAPITALIZATION"],
    "volume_int": ["VOLTODAY", "NUMTRADES", "NUMBIDS", "NUMOFFERS"],
}

# Правила распределения финансовых полей по группам отображения.
# Используются MoexTableModel для точечного применения стилей форматирования.
FORMAT_GROUPS: dict[str, list[str]] = {
    "price_2dp": [
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
    "percent": [
        "LASTCHANGEPRCNT",
        "LASTTOPREVPRICE",
        "WAPTOPREVWAPRICEPRCNT",
        "SPREAD",
    ],
    "integer_volume": [
        "VOLTODAY",
        "NUMTRADES",
        "BIDDEPTH",
        "OFFERDEPTH",
        "BIDDEPTHT",
        "OFFERDEPTHT",
        "NUMBIDS",
        "NUMOFFERS",
    ],
    "large_money": [
        "VALTODAY_RUR",
        "ISSUECAPITALIZATION",
    ],
}
