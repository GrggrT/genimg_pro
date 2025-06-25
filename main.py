# main.py

import sys
from PySide6.QtWidgets import QApplication

# 1. Первым делом — проверка и настройка базы данных.
# Это гарантирует, что БД всегда будет в правильном состоянии перед тем,
# как любой другой модуль попытается к ней обратиться.
from setup_database import setup_database
print("Запуск проверки и инициализации базы данных...")
setup_database()
print("База данных готова к работе.")


# 2. Импортируем все "строительные блоки" нашего приложения.
from gui.main_window import MainWindow
from core.view_model import ViewModel
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient
from core.image_generator import ImageGenerator


def main():
    """
    Главная функция для инициализации и запуска приложения.
    Собирает все компоненты по архитектуре MVVM.
    """
    # Создаем основной объект приложения
    app = QApplication(sys.argv)

    # --- Сборка компонентов ---
    # Создаем экземпляры всех наших классов
    main_window = MainWindow()
    cache_manager = CacheManager()
    api_client = ApiFootballClient()
    image_generator = ImageGenerator()

    # Создаем ViewModel и внедряем в него все зависимости.
    # ViewModel будет оркестром, управляющим всеми остальными частями.
    view_model = ViewModel(
        main_window=main_window,
        cache_manager=cache_manager,
        api_client=api_client,
        image_generator=image_generator
    )

    # --- Соединение ключевых сигналов ---
    # Соединяем сигнал из ViewModel о том, что картинка готова,
    # со слотом в MainWindow, который её отобразит.
    view_model.image_generated.connect(main_window.display_image)

    # Соединяем глобальный сигнал приложения "о скором выходе"
    # с нашим методом для безопасной остановки фоновых потоков.
    app.aboutToQuit.connect(view_model.shutdown)


    # --- Запуск ---
    # Показываем главное окно
    main_window.show()

    # Запускаем главный цикл событий приложения и ожидаем его завершения
    sys.exit(app.exec())


if __name__ == "__main__":
    # Эта строка — стандартная точка входа в Python-приложениях.
    # Она гарантирует, что функция main() будет вызвана только тогда,
    # когда этот файл запускается напрямую.
    main()