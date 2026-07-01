import sys

from loguru import logger
from PySide6.QtWidgets import QApplication

from src.api.client import MoexAPIError, MoexClient
from src.core.logger_config import init_logger
from src.views.main_window import MainWindow


def main():
    # Первое действие при старте — включаем логи
    init_logger()
    logger.info("Инициализация графического интерфейса скринера акций MOEX...")

    # Создаем экземпляр нашего нового клиента
    client = MoexClient()

    try:
        # Пробуем скачать и сразу провалидировать структуру биржи
        data = client.get_clean_data() # noqa: F841
        logger.success("Сетевой уровень работает успешно.")
    except MoexAPIError as e:
        logger.error(f"Тест провален. Сетевой уровень поймал ошибку: {e}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    logger.success("Приложение успешно запущено и готово к работе.")

    # Запуск цикла обработки событий Qt и и сохраняем код возврата (0 — если всё ок)
    exit_code = app.exec()

    # Логируем закрытие приложения перед выходом из Python
    logger.info(f"Цикл обработки событий Qt завершен. Код выхода: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
