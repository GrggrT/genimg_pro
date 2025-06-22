# core/view_model.py
from PySide6.QtCore import QObject, Slot
from gui.main_window import MainWindow
# from core.cache_manager import CacheManager # Раскомментируйте, когда CacheManager будет готов

class ViewModel(QObject):
    """
    ViewModel соединяет View (GUI) и Model (логику).
    """
    def __init__(self, main_window: MainWindow):
        """
        Инициализирует ViewModel.

        :param main_window: Экземпляр главного окна.
        """
        super().__init__()
        self.main_window = main_window
        # self.cache_manager = CacheManager() # Создание экземпляра CacheManager

        # Соединяем сигналы и слоты
        self.main_window.generate_button.clicked.connect(self.on_generate_button_clicked)

    @Slot()
    def on_generate_button_clicked(self):
        """
        Обработчик нажатия кнопки "Сгенерировать изображение".
        """
        team1 = self.main_window.team1_input.text()
        team2 = self.main_window.team2_input.text()

        print(f"Кнопка 'Сгенерировать' нажата.")
        print(f"Команда 1: {team1}")
        print(f"Команда 2: {team2}")

        # Пример взаимодействия с CacheManager
        # print("Поиск в кэше:")
        # result = self.cache_manager.search_team(team1) # Условный вызов
        # print(f"Результат для '{team1}': {result}")