# main.py
import sys
from PySide6.QtWidgets import QApplication

# --- ШАГ 1: ПРОВЕРКА И СОЗДАНИЕ БАЗЫ ДАННЫХ ---
# Мы импортируем и запускаем настройку базы данных ПЕРЕД тем,
# как импортировать остальные части программы. Это гарантирует,
# что база данных всегда будет в правильном состоянии.
from setup_database import create_database
print("Запуск проверки и инициализации базы данных...")
create_database()
print("База данных готова к работе.")
# ----------------------------------------------------


# --- ШАГ 2: ИМПОРТ ОСТАЛЬНЫХ КОМПОНЕНТОВ ---
# Теперь, когда мы уверены, что БД существует и имеет нужные таблицы,
# мы можем безопасно импортировать всё остальное.
from gui.main_window import MainWindow
# Предполагается, что эти классы будут предоставлены Gemini-Core
from core.view_model import ViewModel
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient
from config import DATABASE_PATH, APIFOOTBALL_KEY
from core.image_generator import ImageGenerator


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
    api_client = ApiFootballClient(APIFOOTBALL_KEY)
    image_generator = ImageGenerator()

    # 3. Создаем ViewModel и внедряем в него все зависимости.
    # Этот подход (Dependency Injection) делает код более модульным и тестируемым.
    view_model = ViewModel(
        main_window,
        cache_manager,
        api_client,
        image_generator
    )

    # 4. Отображаем главный интерфейс
    main_window.show()

    # 5. Запускаем цикл событий и выходим, когда он завершится
    sys.exit(app.exec())


if __name__ == "__main__":
    # Запускаем основную функцию приложения
    main()
