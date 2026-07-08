"""Глобальные константы, перечисления и справочники Скринера Московской Биржи.

Данный модуль консолидирует конфигурации пресетов колонок, правила локализации
системных заголовков MOEX ISS API и группы форматирования финансовых данных
для слоя графического интерфейса (View/Model). Использует перечисления Enum
для исключения технического долга в виде "магических строк".
"""

from enum import Enum


class MoexColumns(str, Enum):
    """Строгие идентификаторы колонок MOEX ISS API.
    
    Служит единой точкой правки при изменении спецификации ответов Московской
    Биржи. Защищает конвейеры парсинга, фильтрации и форматирования от опечаток.
    """

    # Идентификаторы и базовые поля
    SECID = "SECID"
    SHORTNAME = "SHORTNAME"
    ISIN = "ISIN"
    LISTLEVEL = "LISTLEVEL"
    
    # Объемы торгов и масштабы эмитента
    ISSUECAPITALIZATION = "ISSUECAPITALIZATION"
    VOLTODAY = "VOLTODAY"
    VALTODAY_RUR = "VALTODAY_RUR"
    NUMTRADES = "NUMTRADES"
    
    # Ценовые экстремумы и расчетные показатели сессии
    OPEN = "OPEN"
    HIGH = "HIGH"
    LOW = "LOW"
    LAST = "LAST"
    PREVPRICE = "PREVPRICE"
    WAPRICE = "WAPRICE"
    PREVWAPRICE = "PREVWAPRICE"
    
    # Показатели ценовой динамики (Моментум)
    LASTCHANGEPRCNT = "LASTCHANGEPRCNT"
    LASTTOPREVPRICE = "LASTTOPREVPRICE"
    WAPTOPREVWAPRICEPRCNT = "WAPTOPREVWAPRICEPRCNT"

    # Параметры ликвидности и котировки стакана
    BID = "BID"
    OFFER = "OFFER"
    SPREAD = "SPREAD"
    HIGHBID = "HIGHBID"
    LOWOFFER = "LOWOFFER"
    
    # Глубина очереди заявок (Рыночная микроструктура)
    BIDDEPTH = "BIDDEPTH"
    OFFERDEPTH = "OFFERDEPTH"
    BIDDEPTHT = "BIDDEPTHT"
    OFFERDEPTHT = "OFFERDEPTHT"
    NUMBIDS = "NUMBIDS"
    NUMOFFERS = "NUMOFFERS"
    
    # Системные флаги и операционные статусы
    TRADINGSTATUS = "TRADINGSTATUS"
    TRADINGSESSION = "TRADINGSESSION"


class MoexBlocks(str, Enum):
    """Идентификаторы корневых табличных блоков в JSON-ответах MOEX ISS API.
    
    Используется для десериализации структурированных массивов биржевых данных.
    """

    SECURITIES = "securities"
    MARKETDATA = "marketdata"
    DATAVERSION = "dataversion"
    MARKETDATA_YIELDS = "marketdata_yields"

# Пресет 1. Базовые колонки для экспресс-анализа (Минимальный сетевой трафик)
DEFAULT_COLUMNS: list[str] = [
    MoexColumns.SECID.value,
    MoexColumns.SHORTNAME.value,
    MoexColumns.LAST.value,
    MoexColumns.LASTTOPREVPRICE.value,
    MoexColumns.VALTODAY_RUR.value,
]

# Пресет 2. Профессиональные метрики (Анализ ликвидности и микроструктуры стакана)
PROFESSIONAL_COLUMNS: list[str] = [
    # Идентификаторы бумаги
    MoexColumns.SECID.value,
    MoexColumns.SHORTNAME.value,
    MoexColumns.ISIN.value,
    MoexColumns.LISTLEVEL.value,
    # Объемы торгов и масштабы эмитента
    MoexColumns.ISSUECAPITALIZATION.value,
    MoexColumns.VOLTODAY.value,
    MoexColumns.VALTODAY_RUR.value,
    MoexColumns.NUMTRADES.value,
    # Ценовые экстремумы текущей сессии
    MoexColumns.OPEN.value,
    MoexColumns.HIGH.value,
    MoexColumns.LOW.value,
    MoexColumns.LAST.value,
    MoexColumns.PREVPRICE.value,
    # Скорость и изменение (Моментум)
    MoexColumns.LASTCHANGEPRCNT.value,
    MoexColumns.LASTTOPREVPRICE.value,
    # Параметры ликвидности (Очередь заявок)
    MoexColumns.BID.value,
    MoexColumns.OFFER.value,
    MoexColumns.SPREAD.value,
    MoexColumns.BIDDEPTHT.value,
    MoexColumns.OFFERDEPTHT.value,
    MoexColumns.NUMBIDS.value,
    MoexColumns.NUMOFFERS.value,
    # Системные флаги торговой сессии
    MoexColumns.TRADINGSTATUS.value,
    MoexColumns.TRADINGSESSION.value,
]

# Справочник локализации системных полей MOEX ISS API для шапки таблицы GUI
COLUMN_MAPPING: dict[str, str] = {
    MoexColumns.SECID.value: "Тикер",
    MoexColumns.SHORTNAME.value: "Наименование",
    MoexColumns.ISIN.value: "Международный код (ISIN)",
    MoexColumns.LISTLEVEL.value: "Уровень листинга",
    MoexColumns.ISSUECAPITALIZATION.value: "Рыночная капитализация",
    MoexColumns.VOLTODAY.value: "Объем торгов (шт.)",
    MoexColumns.VALTODAY_RUR.value: "Оборот торгов (руб.)",
    MoexColumns.NUMTRADES.value: "Количество сделок",
    MoexColumns.OPEN.value: "Цена открытия",
    MoexColumns.HIGH.value: "Дневной максимум",
    MoexColumns.LOW.value: "Дневной минимум",
    MoexColumns.LAST.value: "Цена последней сделки",
    MoexColumns.PREVPRICE.value: "Цена закрытия вчера",
    MoexColumns.LASTTOPREVPRICE.value: "Изменение к закрытию (%)",
    MoexColumns.LASTCHANGEPRCNT.value: "Изменение к открытию (%)",
    MoexColumns.BID.value: "Лучший спрос (BID)",
    MoexColumns.OFFER.value: "Лучшее предложение (OFFER)",
    MoexColumns.SPREAD.value: "Абсолютный спред",
    MoexColumns.WAPRICE.value: "Средневзвешенная цена (VWAP)",
    MoexColumns.PREVWAPRICE.value: "Вчерашняя средневзвешенная цена",
    MoexColumns.WAPTOPREVWAPRICEPRCNT.value: "Изменение средневзвешенной (%)",
    MoexColumns.BIDDEPTH.value: "Доступный спрос",
    MoexColumns.OFFERDEPTH.value: "Доступное предложение",
    MoexColumns.BIDDEPTHT.value: "Суммарный спрос в стакане",
    MoexColumns.OFFERDEPTHT.value: "Суммарное предложение в стакане",
    MoexColumns.NUMBIDS.value: "Заявок на покупку",
    MoexColumns.NUMOFFERS.value: "Заявок на продажу",
    MoexColumns.TRADINGSTATUS.value: "Статус торгов",
    MoexColumns.TRADINGSESSION.value: "Тип сессии",
    MoexColumns.HIGHBID.value: "Наивысший BID",
    MoexColumns.LOWOFFER.value: "Наинизший OFFER",
}

# Агрегированные правила распределения полей по математическим группам отображения.
# Используется в MoexTableModel для применения точечных делегатов и стилей округления.
FORMAT_GROUPS: dict[str, list[str]] = {
    "price_2dp": [
        MoexColumns.LAST.value,
        MoexColumns.OPEN.value,
        MoexColumns.HIGH.value,
        MoexColumns.LOW.value,
        MoexColumns.PREVPRICE.value,
        MoexColumns.BID.value,
        MoexColumns.OFFER.value,
        MoexColumns.HIGHBID.value,
        MoexColumns.LOWOFFER.value,
        MoexColumns.WAPRICE.value,
        MoexColumns.PREVWAPRICE.value,
    ],
    "percent": [
        MoexColumns.LASTCHANGEPRCNT.value,
        MoexColumns.LASTTOPREVPRICE.value,
        MoexColumns.WAPTOPREVWAPRICEPRCNT.value,
        MoexColumns.SPREAD.value,
    ],
    "integer_volume": [
        MoexColumns.VOLTODAY.value,
        MoexColumns.NUMTRADES.value,
        MoexColumns.BIDDEPTH.value,
        MoexColumns.OFFERDEPTH.value,
        MoexColumns.BIDDEPTHT.value,
        MoexColumns.OFFERDEPTHT.value,
        MoexColumns.NUMBIDS.value,
        MoexColumns.NUMOFFERS.value,
    ],
    "large_money": [
        MoexColumns.VALTODAY_RUR.value,
        MoexColumns.ISSUECAPITALIZATION.value,
    ],
}
