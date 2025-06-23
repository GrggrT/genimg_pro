# main.py
import sys
from PySide6.QtWidgets import QApplication

# Импортируем наши компоненты
from gui.main_window import MainWindow
# Предполагается, что класс ViewModel будет предоставлен Gemini-Core
# в соответствии с архитектурой проекта.
from core.view_model import ViewModel


def main():
    """
    Главная точка входа в приложение GenImg Pro.

    Эта функция выполняет следующие шаги:
    1. Создает экземпляр приложения QApplication.
    2. Создает View (главное окно MainWindow).
    3. Создает ViewModel и связывает его с View. ViewModel является "мозгом"
       приложения и управляет всей логикой.
    4. Отображает окно приложения.
    5. Запускает главный цикл событий приложения.
    """
    # 1. Создаем экземпляр приложения
    app = QApplication(sys.argv)

    # 2. Создаем View (Представление)
    main_window = MainWindow()

    # 3. Создаем ViewModel и связываем его с View
    # ViewModel получает ссылку на View, чтобы подписываться на его сигналы
    # и вызывать его слоты для обновления интерфейса.
    # Переменная view_model не используется напрямую, но ее создание
    # запускает всю логику связывания в ее конструкторе.
    view_model = ViewModel(view=main_window)

    # 4. Отображаем главный интерфейс
    main_window.show()

    # 5. Запускаем цикл событий и выходим, когда он завершится
    sys.exit(app.exec())


if __name__ == "__main__":
    # Запускаем основную функцию приложения
    main()
