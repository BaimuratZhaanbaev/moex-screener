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
    
    # Запуск цикла обработки событий Qt
    sys.exit(app.exec())

if __name__ == "__main__":
    main()