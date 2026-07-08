from typing import Any

from loguru import logger

from src.core.constants import MoexBlocks


class MoexSchemaExtractor:
    """Сервис автоматического анализа метаданных и динамических схем типов MOEX."""

    @staticmethod
    def extract_numeric_columns(raw_data: dict[str, Any]) -> set[str]:
        """Сканирует метаданные ответов и формирует множество имен числовых полей."""
        numeric_fields: set[str] = set()

        # Сканируем оба обязательных блока по ключам из Enum
        for block_key in (MoexBlocks.SECURITIES, MoexBlocks.MARKETDATA):
            block = raw_data.get(block_key.value, {})
            metadata = block.get("metadata", {})

            if not metadata:
                continue

            for col_name, info in metadata.items():
                data_type = info.get("type", "").lower()
                # Если тип соответствует спецификации числа на Мосбирже
                if "double" in data_type or "int" in data_type or "float" in data_type:
                    numeric_fields.add(col_name)

        logger.debug(f"Экстрактор определил {len(numeric_fields)} числовых полей.")
        return numeric_fields
    