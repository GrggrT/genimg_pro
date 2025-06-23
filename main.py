# main.py
import sys
from PySide6.QtWidgets import QApplication

# Импортируем наши компоненты
from gui.main_window import MainWindow
# Предполагается, что эти классы будут предоставлены Gemini-Core
from core.view_model import ViewModel
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient


def main():
    """
    Главная точка входа в приложение GenImg Pro.

    Эта функция выполняет следующие шаги:
    1. Создает экземпляр приложения QApplication.
    2. Инициализирует все необходимые зависимости (View, CacheManager, ApiClient).
    3. Создает ViewModel и внедряет в него зависимости.
    4. Отображает окно приложения.
    5. Запускает главный цикл событий приложения.
    """
    # 1. Создаем экземпляр приложения
    app = QApplication(sys.argv)

    # 2. Инициализируем все компоненты-зависимости
    main_window = MainWindow()
    cache_manager = CacheManager()
    # Убедитесь, что API ключ для ApiFootballClient доступен в .env файле
    api_client = ApiFootballClient()

    # 3. Создаем ViewModel и внедряем в него все зависимости.
    # Этот подход (Dependency Injection) делает код более модульным и тестируемым.
    view_model = ViewModel(
        view=main_window,
        cache_manager=cache_manager,
        api_client=api_client
    )

    # 4. Отображаем главный интерфейс
    main_window.show()

    # 5. Запускаем цикл событий и выходим, когда он завершится
    sys.exit(app.exec())


if __name__ == "__main__":
    # Запускаем основную функцию приложения
    main()
