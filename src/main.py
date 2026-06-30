import sys
from PySide6.QtWidgets import QApplication
from loguru import logger
from src.core.logger_config import init_logger
from src.views.main_window import MainWindow

def main():
    # Первое действие при старте — включаем логи
    init_logger()
    logger.info("Инициализация графического интерфейса скринера акций MOEX...")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    logger.info("Приложение успешно запущено и готово к работе.")
    
    # Запуск цикла обработки событий Qt и и сохраняем код возврата (0 — если всё ок)
    exit_code = app.exec()

    # Логируем закрытие приложения перед выходом из Python
    logger.info(f"Цикл обработки событий Qt завершен. Код выхода: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()