"""Компонент инспекции и структурного анализа метаданных ответов биржи.

Предоставляет вспомогательный инструментарий для динамического анализа схем данных,
возвращаемых Московской Биржей, изолируя логику определения типов от основного
конвейера десериализации парсера.
"""

from typing import Any

from loguru import logger

from src.core.constants import MoexBlocks


class MoexSchemaExtractor:
    """Сервис автоматического анализа метаданных и динамических схем типов MOEX.
    
    Реализует принцип единственной ответственности путем изоляции алгоритмов
    парсинга типов спецификации ISS API от логики построения матриц Pandas DataFrame.
    """

    @staticmethod
    def extract_numeric_columns(raw_data: dict[str, Any]) -> set[str]:
        """Сканирует секции метаданных ISS API и формирует список числовых полей.

        Последовательно обходит блоки справочной информации и оперативного стакана,
        выявляя типы double, float, int32 и int64 для последующей изоляции пустых
        финансовых значений.

        Args:
            raw_data (dict[str, Any]): 
                Валидный десериализованный JSON-ответ от API MOEX.

        Returns:
            set[str]: 
                Множество системных названий столбцов, подлежащих числовому кастингу.
        """
        numeric_fields: set[str] = set()

        # Итерация по корневым табличным узлам ответа биржи
        for block_key in (MoexBlocks.SECURITIES, MoexBlocks.MARKETDATA):
            block = raw_data.get(block_key.value, {})
            metadata = block.get("metadata", {})

            if not metadata:
                continue

            # Анализ типов данных, задекларированные ядром биржи
            for col_name, info in metadata.items():
                data_type = info.get("type", "").lower()
                
                # Если тип соответствует спецификации числа на Мосбирже
                if "double" in data_type or "int" in data_type or "float" in data_type:
                    numeric_fields.add(col_name)

        logger.debug(f"Экстрактор определил {len(numeric_fields)} числовых полей.")
        return numeric_fields
    