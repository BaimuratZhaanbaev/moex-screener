from typing import Any

import pandas as pd
from loguru import logger
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.core.constants import COLUMN_MAPPING, FORMAT_GROUPS, MoexColumns


class MoexTableModel(QAbstractTableModel):
    """
    Кастомная модель данных Qt для эффективного сопряжения аналитических матриц
    Pandas DataFrame с графическим представлением QTableView.
    """

    def __init__(self, parent: Any | None = None):
        super().__init__(parent)
        # Шаг 1: Инициализация скрытых полей для хранения данных
        self._source_df: pd.DataFrame = pd.DataFrame()  # Эталонный (мастер) массив от биржи
        # Текущий отображаемый срез (отфильтрованный/отсортированный)
        self._df: pd.DataFrame = pd.DataFrame()
        logger.debug("MoexTableModel успешно инициализирована.")

    # Переопределение "Святой Троицы" методов модели Qt
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Возвращает текущее количество строк в видимой таблице."""
        if parent.isValid():
            return 0
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Возвращает текущее количество колонок в видимой таблице."""
        if parent.isValid():
            return 0
        return len(self._df.columns)

    def data(
        self, 
        index: QModelIndex, 
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """
        Поставляет данные ячейкам таблицы.
        Это самый важный, объемный и производительный узел модели.
        Он вызывается движком Qt динамически в реальном времени для каждой видимой
        ячейки при запуске программы и при прокрутке (скроллинге) таблицы.
        """
        if not index.isValid():
            logger.trace("Запрошен невалидный QModelIndex")
            return None

        row: int = index.row()
        col: int = index.column()

        # Защита от выхода за границы DataFrame
        # (если интерфейс и данные рассинхронизировались)
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

            # Универсальное динамическое форматирование на основе групп из config.py
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

            # Текстовые данные прижимаем влево, финансовые/числа — вправо
            if col_name in text_columns:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    # Настройка человекочитаемых заголовков таблицы
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Определяет названия столбцов на верхней панели QTableView."""
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

        col_name: str = self._df.columns[column]
        logger.debug(
            f"Запущена сортировка по колонке: '{col_name}' "
            f"(Индекс: {column}), Направление: {order}"
        )

        # Сигнализируем интерфейсу Qt о начале перестройки структуры строк
        self.layoutAboutToBeChanged.emit()

        ascending: bool = order == Qt.SortOrder.AscendingOrder

        # na_position='last' — критически важное требование!
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
    def set_dataframe(self, new_df: pd.DataFrame):
        """
        Принимает очищенный на DataFrame, обновляет мастер-копию
        и сбрасывает виджет к исходному состоянию.
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
