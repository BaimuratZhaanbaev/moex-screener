# MOEX Screener

Desktop stock screener for MOEX shares using PySide6, pandas, and MOEX ISS API.


<!-- Окружение и Базовый стек -->
[![Python Version](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt)-41CD52.svg?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg?style=flat-square)](#-требования-prerequisites)

<!-- Аналитика, Сеть и Логирование -->
[![Data Processing](https://img.shields.io/badge/Data-Pandas-150458.svg?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Network Client](https://img.shields.io/badge/Network-HTTPX-008080.svg?style=flat-square)](https://www.python-httpx.org/)
[![Logging](https://img.shields.io/badge/Logging-Loguru-BA55D3.svg?style=flat-square)](https://github.com/Delgan/loguru)

<!-- Тестирование и Качество кода -->
[![Core Tests](https://img.shields.io/badge/Tests-PyTest-0A9EDC.svg?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![GUI Tests](https://img.shields.io/badge/Tests%20GUI-PyTest--Qt-blueviolet.svg?style=flat-square&logo=pytest&logoColor=white)](https://pytest-qt.readthedocs.io/)
[![Linter/Formatter](https://img.shields.io/badge/Linter-Ruff-000000.svg?style=flat-square)](https://github.com/astral-sh/ruff)

<!-- DevOps, Шаблонизация и Дистрибуция -->
[![VCS](https://img.shields.io/badge/VCS-Git-F05032.svg?style=flat-square&logo=git&logoColor=white)](https://git-scm.com/)
[![Dependency Manager](https://img.shields.io/badge/Poetry-Package%20Manager-60A5FA.svg?style=flat-square&logo=poetry&logoColor=white)](https://python-poetry.org/)
[![Project Template](https://img.shields.io/badge/Template-Copier-FF5A5F.svg?style=flat-square)](https://copier.readthedocs.io/)
[![Compiler](https://img.shields.io/badge/Build-PyInstaller-F39C12.svg?style=flat-square&logo=python&logoColor=white)](https://pyinstaller.org/)

---

## 🎯 Ключевые возможности (Features)
* **Real-time Data:** Автоматическая загрузка справочных и рыночных данных с Московской Биржи через ISS API.
* **Высокая производительность:** Векторизованная фильтрация таблиц средствами `pandas` со сложностью по памяти $O(1)$.
* **Гибкий интерфейс:** Переключение табличных пресетов (Базовый, Профессиональный) и динамический парсинг схем данных.
* **Надежность:** Автономное логирование с ротацией файлов и защита от сбоев в окружении Windows (`--noconsole` safe).

## 💻 Требования (Prerequisites)
* **Операционная система:** Windows 10/11 (сборка протестирована локально), Linux / macOS (архитектурная совместимость).
* **Интерпретатор:** Python версии `3.11` — `3.13`.
* **Менеджер пакетов:** Poetry.

## 📥 Установка и запуск (для пользователей)

Приложение поставляется в формате **Portable (один файл)** и не требует установки Python или дополнительных библиотек.

1. Перейдите в раздел **Releases** на GitHub.
2. Скачайте файл `screener.exe`.
3. Запустите скачанный файл двойным кликом.

## 🚀 Быстрый старт (Quick Start)

1. Клонирование репозитория и установка зависимостей:

   ```bash
   git clone https://github.com/BaimuratZhaanbaev/moex-screener.git
   cd moex-screener
   poetry install
   ```

2. Запуск приложения:

    ```Bash
    poetry run screener
    # или напрямую через интерпретатор:
    poetry run python src/main.py
    ```

3. Запуск тестов:
    
    ```Bash
    poetry run pytest
    ```

## 📂 Структура проекта (Project Structure)

```text
moex-screener/                            # Корневая директория проекта (Скринер Московской Биржи)
│
├── src/                                  # ИСХОДНЫЙ КОД ПРИЛОЖЕНИЯ (Основная логика)
│   ├── main.py                           # Точка входа в приложение (запуск главного цикла Qt/GUI)
│   ├── __init__.py                       # Маркер пакета инициализации исходного кода
│   │
│   ├── api/                              # Модуль сетевого взаимодействия
│   │   ├── client.py                     # HTTP-клиент (Httpx) для ISS API Мосбиржи (запросы, обработка ошибок связи)
│   │   └── __init__.py                   # Экспорт кастомных исключений (например, MoexAPIError) и клиента
│   │
│   ├── core/                             # ЯДРО ПРИЛОЖЕНИЯ (Бизнес-логика и системные компоненты)
│   │   ├── analytics.py                  # Вычислительные функции, математические расчёты и аналитические метрики
│   │   ├── config.py                     # Управление глобальными настройками (пути, таймауты, параметры сессии)
│   │   ├── constants.py                  # Константные данные (списки колонок: DEFAULT_COLUMNS, PROFESSIONAL_COLUMNS)
│   │   ├── logger_config.py              # Настройка логирования приложения с помощью библиотеки Loguru
│   │   ├── parser.py                     # MoexDataParser (десериализация JSON от биржи, конвертация и сборка в Pandas DataFrame)
│   │   ├── extractor.py                  # MoexSchemaExtractor (автоматический анализ метаданных и динамических схем типов ISS API)
│   │   └── __init__.py                   # Инициализация ядра системы
│   │
│   ├── models/                           # Модели отображения данных (Архитектура Qt MVC / Model-View)
│   │   ├── table_model.py                # MoexTableModel (наследник QAbstractTableModel для эффективной связи DataFrame с UI)
│   │   └── __init__.py                   # Инициализация слоя моделей данных
│   │
│   ├── resources/                        # Статические ресурсы приложения
│   │   ├── moex_screener_icon.ico        # Иконка приложения в формате .ico
│   │   ├── moex_screener_icon.png        # Иконка приложения в формате .png
│   │   └── styles.qss                    # Каскадные таблицы стилей Qt (дизайн, цвета, шрифты графического интерфейса)
│   │
│   └── views/                            # ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (Слой визуализации / View)
│       ├── components.py                 # Кастомные мелкие UI-виджеты (кнопки, поля ввода, индикаторы)
│       ├── filter_panel.py               # Панель фильтрации (ввод тикера, выбор режима отображения, кнопка обновления)
│       ├── main_window.py                # MainWindow (главное окно: компоновка слоев, привязка таблицы QTableView и сигналов)
│       └── __init__.py                   # Инициализация слоя графического интерфейса
│
├── tests/                                # МОДУЛЬНОЕ И ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ (PyTest + PyTest-Qt)
│   ├── conftest.py                       # Глобальные фикстуры тестов (генерация эталонных данных, создание окон для qtbot)
│   ├── test_analytics.py                 # Тестирование математических формул и аналитических расчётов
│   ├── test_api.py                       # Тесты сетевого клиента (проверка таймаутов, падения интернета, валидности JSON)
│   ├── test_filter_panel.py              # Изолированные тесты элементов UI панели управления
│   ├── test_main_window.py               # Интеграционные тесты главного окна (сквозная проверка фильтрации, сброса, сортировки)
│   ├── test_model.py                     # Тестирование поведения таблицы MoexTableModel (возврат индексов, обработка NaN)
│   ├── test_parser.py                    # Тестирование парсера (проверка на битые структуры данных Мосбиржи)
│   ├── test_ui.py                        # Базовые смоук-тесты отрисовки графических компонентов
│   └── __init__.py                       # Инициализация пакета тестов
│
├── data/                                 # ХРАНИЛИЩЕ ДАННЫХ И ФИКСТУР
│   ├── fixtures/                         # JSON-заглушки для тестов (валидные данные, пустые, коррумпированные, без колонок)
│   └── reference/                        # Статичные эталонные файлы
│       └── master_market_data.csv        # Локальный бэкап рыночных данных для работы в офлайн-режиме
│
├── assets/                               # Дополнительные ресурсы
│   └── style.css                         # Стили для HTML-отчетов (используются плагином pytest-html)
│
├── logs/                                 # Системные логи времени выполнения
│   └── moex_screener.log                 # Файл, куда Loguru пишет трассировку ошибок, предупреждения и INFO-сообщения
│
├── .gitignore                            # Конфигурация Git (исключает из коммитов папки кэша, логи и виртуальное окружение)
├── LICENSE                               # Юридическое соглашение / Лицензия на использование кода проекта
├── poetry.lock                           # Фиксация точных версий всех установленных Python-пакетов и их зависимостей
├── pyproject.toml                        # Главный файл конфигурации Poetry (зависимости, настройки сборщика ruff/pytest)
└── README.md                             # Документация проекта для разработчиков (инструкция по установке, описание архитектуры)
```

## 🔬 Модульное и интеграционное тестирование (`pytest`)

В проекте используется фреймворк `pytest` совместно с плагином `pytest-qt` для изолированного тестирования бизнес-логики (`pandas`) и графических моделей (`PySide6`).

Для запуска тестов в различных режимах используйте следующие команды:

#### 1. Базовый запуск

Запуск всех тестов в проекте в стандартном режиме:

```bash
poetry run pytest
```

#### 2. Подробный (Verbose) режим

Выводит подробную информацию: имя каждого тест-кейса, его модуль и статус выполнения (`PASSED`/`FAILED`). **Рекомендуется для отчетов по практике:**

```bash
poetry run pytest -v
```

#### 3. Запуск конкретного тестового файла

Если вы работаете над отдельным модулем и не хотите ждать прогона всей тестовой базы:

```bash
# Запуск только тестов фильтрации и аналитики Pandas
poetry run pytest tests/test_analytics.py -v

# Запуск только тестов кастомной Qt-модели таблицы
poetry run pytest tests/test_model.py -v
```

#### 4. Запуск конкретного теста (по имени функции)

Позволяет изолированно отлаживать один целевой тест-кейс:

```bash
poetry run pytest tests/test_analytics.py::test_strict_zero_change_vs_null -v
```

#### 5. Остановка при первой ошибке (`-x`)

Флаг `-x` (maxfail=1) мгновенно прерывает сессию тестирования, как только один из тестов падает. Удобно при TDD-разработке и рефакторинге:

```bash
poetry run pytest -v -x
```

#### 6. Вывод отладочной печати (`-s`)

По умолчанию `pytest` перехватывает и скрывает всё, что пишется в `stdout` (например, вызовы `print()` или логи). Этот флаг заставляет отображать консольный вывод внутри тестов:

```bash
poetry run pytest -v -s
```

---


## 🛠️ Качество кода и стандарты разработки (Ruff)

В проекте используется **Ruff** для автоматического форматирования кода и статического анализа (поиска ошибок, неиспользуемых импортов и нарушений стиля PEP 8). 

Перед каждым коммитом разработчик **обязан** проверить свой код.

### 🚀 Команды для терминала

1. **Автоматическое форматирование кода** (заменяет Black/isort, выравнивает отступы, сортирует импорты):

```bash
poetry run ruff format .
```

2. **Статический анализ и поиск ошибок** (линтер):

```bash
poetry run ruff check .
```

3. **Автоматическое исправление безопасных ошибок** (удаление неиспользуемых импортов, исправление простых нарушений):

```bash
poetry run ruff check . --fix
```

## Credits
* Icon made by [srip](https://flaticon.com) from [://flaticon.com](https://://flaticon.com/)
