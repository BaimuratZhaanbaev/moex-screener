"""Управление конфигурациями и пользовательскими настройками сессии.

Отвечает за хранение состояний отображения, пресетов колонок таблиц
и локальных параметров визуализации GUI.
"""

from src.core.constants import DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS


class UIConfig:
    """Менеджер конфигурации отображения данных в табличной сетке."""

    def __init__(self):
        """Инициализирует базовые параметры отображения по умолчанию."""
        # Текущий режим видимости колонок. Варианты: 'basic', 'professional', 'full'
        self.current_mode = "basic"

        # Резервная копия списка колонок для кастомизации пользователем
        self.custom_visible_columns = DEFAULT_COLUMNS.copy()

    def get_columns_to_show(self, all_available_columns: list[str]) -> list[str]:
        """Формирует финальный список видимых колонок для QTableView.

        Сопоставляет выбранный пресет отображения со списком колонок,
        фактически присутствующих в текущем ответе биржи, исключая несуществующие поля.

        Args:
            all_available_columns (list[str]): Список колонок, содержащихся
                в активном DataFrame после парсинга.

        Returns:
            list[str]: Отфильтрованный список системных имён колонок, разрешённых
                к отрисовке в графическом интерфейсе.
        """

        if self.current_mode == "basic":
            return [col for col in DEFAULT_COLUMNS if col in all_available_columns]

        elif self.current_mode == "professional":
            return [col for col in PROFESSIONAL_COLUMNS if col in all_available_columns]

        # В режиме 'full' возвращаем кастомный набор либо абсолютно все доступные поля
        return (
            self.custom_visible_columns
            if self.custom_visible_columns
            else all_available_columns
        )
