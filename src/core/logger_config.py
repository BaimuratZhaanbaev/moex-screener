import sys
from pathlib import Path
from loguru import logger

def init_logger():
    """Выполняет первоначальную настройку Loguru под требования проекта."""
    # Очищаем стандартный вывод Loguru, чтобы задать свои правила
    logger.remove()

    # Определяем путь к папке с логами в корне проекта
    # Path(__file__).parents[2] поднимается из src/core/ до корня moex_screener/
    log_dir = Path(__file__).parents[2] / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "moex_screener.log"

    # 1. Настройка вывода в терминал (консоль IDE) — яркий, цветной, для разработки
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"  # В консоли во время разработки хотим видеть всё, включая дебаг
    )

    # 2. Настройка записи в файл — строгий продакшн-формат с архивацией
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",         # В файл пишем только важные события (INFO, WARNING, ERROR)
        rotation="5 MB",      # Как только файл достигает 5 МБ, создается новый, а старый архивируется
        retention="7 days",   # Хранить логи только за последнюю неделю (чтобы не забивать диск)
        compression="zip",    # Старые логи автоматически сжимаются в ZIP-архив
        enqueue=True,         # ВАЖНО: включает асинхронную и безопасную работу из фоновых потоков QThread
        encoding="utf-8"      # Гарантирует корректное отображение кириллицы
    )

    logger.info("Система логирования Loguru успешно инициализирована.")