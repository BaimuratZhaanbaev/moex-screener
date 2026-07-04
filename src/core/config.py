from src.core.constants import DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS


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
