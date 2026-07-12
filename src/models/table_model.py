"""Компонент отображения данных в архитектуре Qt Model-View (MVC).

Предоставляет кастомную табличную модель, связывающую высокопроизводительные
матрицы Pandas DataFrame с графическими виджетами PySide6 (QTableView)
с обеспечением локализации, форматирования финансовых чисел и сортировки.
"""

from typing import Any

import pandas as pd
from loguru import logger
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.core.constants import COLUMN_MAPPING, FORMAT_GROUPS, MoexColumns


class MoexTableModel(QAbstractTableModel):
    """Кастомная модель данных Qt для сопряжения таблиц Pandas с QTableView.
    
    Обеспечивает реактивное обновление интерфейса, потокобезопасный сброс
    состояний и форматирование биржевых метрик в реальном времени.
    """

    def __init__(self, parent: Any | None = None):
        """Инициализирует пустую модель данных и резервирует структуры Pandas.

        Args:
            parent (Any | None, optional): Родительский Qt-объект для управления
                памятью в иерархии QObject. По умолчанию None.
        """
        super().__init__(parent)
        self._source_df: pd.DataFrame = pd.DataFrame()  # Эталонный массив от биржи
        self._df: pd.DataFrame = pd.DataFrame() # Отфильтрованный срез для отрисовки
        logger.debug("MoexTableModel успешно инициализирована.")

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """"Возвращает текущее количество строк в активном срезе данных.

        Args:
            parent (QModelIndex, optional): Индекс родительского элемента
                (используется в древовидных структурах). По умолчанию пустой.

        Returns:
            int: Число строк, доступных для отрисовки.
        """
        if parent.isValid():
            return 0
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Возвращает текущее количество колонок в активном срезе данных.

        Args:
            parent (QModelIndex, optional): Индекс родительского элемента.
                По умолчанию пустой.

        Returns:
            int: Число столбцов, доступных для отрисовки.
        """
        if parent.isValid():
            return 0
        return len(self._df.columns)

    def data(
        self, 
        index: QModelIndex, 
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Поставляет отформатированные финансовые данные в ячейки QTableView.

        Вызывается ядром Qt динамически при отрисовке и скроллинге. Оптимизирован
        для предотвращения задержек интерфейса (UI Lag) при работе с большими матрицами.

        Args:
            index (QModelIndex): Координаты запрашиваемой ячейки (строка/колонка).
            role (int, optional): Роль запроса данных (отображение, выравнивание, цвет).
                По умолчанию DisplayRole.

        Returns:
            Any: Строковое представление, флаг выравнивания или None, если роль не поддерживается.
        """
        if not index.isValid():
            logger.trace("Запрошен невалидный QModelIndex")
            return None

        row: int = index.row()
        col: int = index.column()

        # Защитный барьер против гонки данных при асинхронном обновлении
        if row >= len(self._df) or col >= len(self._df.columns):
            logger.warning(
                f"Индекс Qt [{row}, {col}] "
                f"вышел за границы DataFrame ({self._df.shape})"
            )
            return None

        col_name: str = self._df.columns[col]
        val: Any = self._df.iloc[row, col]

        logger.trace(
            f"Запрос ячейки [{row}, {col}] ({col_name}), значение: {val}, роль: {role}"
        )

        # 1. Отображение текста в ячейках (DisplayRole)
        if role == Qt.ItemDataRole.DisplayRole:
            # Корректная обработка null значений
            if pd.isna(val) or val is None:
                logger.trace(
                    f"Ячейка [{row}, {col}]: "
                    f"обнаружено null-значение, заменяем на прочерк"
                )
                return "-"

            # Безопасное форматирование через извлечение списков по ключам
            if col_name in FORMAT_GROUPS.get("price_2dp", []):
                return f"{val:,.2f}".replace(",", " ")

            if col_name in FORMAT_GROUPS.get("percent", []):
                return f"{val:+.2f}%"

            if col_name in FORMAT_GROUPS.get("integer_volume", []):
                return f"{int(val):,}".replace(",", " ")

            if col_name in FORMAT_GROUPS.get("large_money", []):
                return f"{val:,.0f}".replace(",", " ")

            return str(val)

        # 2. Форматирование выравнивания (TextAlignmentRole)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            text_columns = {
                MoexColumns.SECID.value, 
                MoexColumns.SHORTNAME.value, 
                MoexColumns.ISIN.value,
            }

            if col_name in text_columns:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            
            # Финансовые показатели и объёмы всегда выравниваем по правому краю
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Конфигурирует человекочитаемые русскоязычные заголовки столбцов.

        Args:
            section (int): Индекс столбца или строки.
            orientation (Qt.Orientation): Направление заголовка (Horizontal/Vertical).
            role (int, optional): Роль отображения. По умолчанию DisplayRole.

        Returns:
            Any: Локализованная строка заголовка из COLUMN_MAPPING или None.
        """
        logger.trace(
            f"Запрос заголовка: секция={section}, ориентация={orientation}, роль={role}"
        )

        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if not self._df.empty and section < len(self._df.columns):
                technical_name: str = self._df.columns[section]

                # русский перевод из маппинга или техническое имя как резерв
                display_name: str = COLUMN_MAPPING.get(technical_name, technical_name)

                logger.trace(
                    f"Успешный маппинг заголовка: {technical_name} -> '{display_name}'"
                )
                return display_name
            else:
                logger.warning(
                    f"Запрос заголовка вышел за границы данных! "
                    f"Индекс секции: {section}, "
                    f"доступно колонок в DataFrame: {len(self._df.columns)}"
                )

        return None

    # Реализация алгоритма быстрой сортировки
    def sort(
        self, 
        column: int, 
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
    ) -> None:
        """Выполняет мгновенную сортировку строк в Pandas."""
        if self._df.empty:
            logger.debug(
                "Биржа еще не прислала данные или они не загрузились (DataFrame пустой)"
            )
            return

        # Сигнализируем интерфейсу Qt о начале перестройки структуры строк
        self.layoutAboutToBeChanged.emit()

        if column == -1:
            logger.info(
                "Сброс сортировки: возвращаем строки к исходному порядку по индексу"
            )

            # Сортируем текущий DataFrame по его оригинальному индексу (0, 1, 2...)
            self._df.sort_index(ascending=True, inplace=True)
            self.layoutChanged.emit()
            return
        
        # Стандартная сортировка по выбранной колонке
        col_name: str = self._df.columns[column]
        logger.debug(
            f"Запущена сортировка по колонке: '{col_name}' "
            f"(Индекс: {column}), Направление: {order}"
        )

        ascending: bool = order == Qt.SortOrder.AscendingOrder

        # Бумаги у которых цена LAST = null при любой сортировке уходят вниз таблицы
        self._df.sort_values(
            by=col_name, 
            ascending=ascending, 
            inplace=True, 
            na_position="last",
        )

        # Уведомляем представление (View) о завершении перерисовки
        self.layoutChanged.emit()

    # Безопасный метод заливки новых данных от АПИ-клиента
    def set_dataframe(self, new_df: pd.DataFrame) -> None:
        """Безопасно атомарно обновляет внутренние матрицы данных парсера.

        Использует встроенный механизм транзакций Qt (beginResetModel/endResetModel),
        чтобы виджеты отображения корректно пересчитали новые размеры и сбросили кэш.

        Args:
            new_df (pd.DataFrame): Очищенный и типизированный DataFrame от MoexDataParser.
        """
        # Гарантируем жесткий сброс модели через встроенные транзакции Qt
        self.beginResetModel()

        # Сохраняем мастер-копию для фильтрации и делаем её активной для отображения
        self._source_df: pd.DataFrame = new_df.copy()
        self._df: pd.DataFrame = new_df

        self.endResetModel()
        logger.info(
            f"Матрица данных обновлена в модели. Загружено строк: {len(self._df)}."
        )
