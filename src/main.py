import os
import sys

from loguru import logger
from PySide6.QtWidgets import QApplication

from src.core.logger_config import init_logger
from src.views.main_window import MainWindow


def load_application_styles(app: QApplication) -> None:
    """Загружает каскадные таблицы стилей (QSS) на уровне всего приложения.
    
    Централизованная настройка гарантирует, что все дочерние окна, диалоги 
    и QMessageBox автоматически унаследуют тему оформления без дублирования кода.
    """
    qss_path = "src/resources/styles.qss"
    
    if not os.path.exists(qss_path):
        logger.warning(
            f"Файл оформления не найден по пути: {qss_path}. "
            "Будет использована стандартная системная тема."
        )
        return

    try:
        with open(qss_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        logger.info(f"Глобальные стили интерфейса успешно применены из {qss_path}")
    except Exception as e:
        logger.error(f"Не удалось прочитать файл стилей {qss_path}: {e}")


def main():
    init_logger()
    logger.info("Запуск ядра скринера акций MOEX...")

    app = QApplication(sys.argv)

    #app.setStyle("Fusion") 
    #load_application_styles(app)

    window = MainWindow()
    window.show()

    logger.success("Приложение успешно запущено и готово к работе.")

    # Запуск цикла обработки событий Qt и и сохраняем код возврата (0 — если всё ок)
    exit_code = app.exec()

    logger.info(f"Цикл обработки событий Qt завершен. Код выхода: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
