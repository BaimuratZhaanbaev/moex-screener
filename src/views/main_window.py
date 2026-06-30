from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QCloseEvent
from loguru import logger

class MainWindow(QMainWindow):
    """Главное окно приложения скринера акций MOEX."""
    
    def __init__(self):
        super().__init__()
        logger.info("Инициализация графических компонентов MainWindow...")
        
        # Настройка параметров окна
        self.setWindowTitle("MOEX Stock Screener")
        self.resize(1000, 600)
        
        # Создаем простейший центральный виджет, чтобы окно не было пустым
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.label = QLabel("Добро пожаловать в MOEX Stock Screener!\nОкружение и логирование настроены успешно.", self)
        self.label.setStyleSheet("font-size: 16px; font-weight: bold; qproperty-alignment: 'AlignCenter';")
        layout.addWidget(self.label)
        
        self.setCentralWidget(central_widget)
        
        # Инициализируем StatusBar (требование ТЗ для вывода ошибок)
        self.statusBar().showMessage("Приложение готово к работе. Сетевой уровень инициализирован.")
        logger.debug("MainWindow успешно отрисовано.")

    def closeEvent(self, event: QCloseEvent):
        """Вызывается автоматически при закрытии главного окна пользователем"""
        logger.info("Пользователь инициировал закрытие главного окна.")
        
        # Здесь в будущем можно добавить логику:
        # Например: self.save_user_settings() или self.http_client.close()
        
        # Разрешаем окну закрыться
        event.accept() 