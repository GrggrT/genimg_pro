# core/view_model.py

from PySide6.QtCore import QObject, Slot
from gui.main_window import MainWindow
from core.cache_manager import CacheManager

class ViewModel(QObject):
    """
    ViewModel соединяет View (GUI) и Model (логику).
    Он обрабатывает действия пользователя, взаимодействует с ядром
    и обновляет представление.
    """
    def __init__(self, main_window: MainWindow, cache_manager: CacheManager):
        """
        Инициализирует ViewModel.

        :param main_window: Экземпляр главного окна (View).
        :param cache_manager: Экземпляр менеджера кэша (Model).
        """
        super().__init__()
        self.main_window = main_window
        self.cache_manager = cache_manager

        # --- Соединение сигналов из View со слотами в ViewModel ---
        self.main_window.generate_clicked.connect(self.on_generate_clicked)
        self.main_window.post_type_changed.connect(self.on_post_type_changed)
        self.main_window.team_input_started.connect(self.on_team_input_started)

    @Slot()
    def on_generate_clicked(self):
        """
        Обработчик сигнала `generate_clicked` из MainWindow.
        Основная логика поиска команд и обратной связи с GUI.
        """
        self.main_window.toggle_generate_button(False)
        self.main_window.set_status_message("Поиск команд в кэше...")

        team1_name = self.main_window.team1_input.text().strip()
        team2_name = self.main_window.team2_input.text().strip()

        if not team1_name or not team2_name:
            self.main_window.set_status_message("Ошибка: Названия обеих команд должны быть заполнены.")
            self.main_window.toggle_generate_button(True)
            return

        team1_found = self.cache_manager.find_team_by_name(team1_name)
        if not team1_found:
            self.main_window.set_status_message(f"Команда '{team1_name}' не найдена в кэше.")
            self.main_window.toggle_generate_button(True)
            return

        team2_found = self.cache_manager.find_team_by_name(team2_name)
        if not team2_found:
            self.main_window.set_status_message(f"Команда '{team2_name}' не найдена в кэше.")
            self.main_window.toggle_generate_button(True)
            return
        
        # Если обе команды найдены
        self.main_window.set_status_message("Обе команды успешно найдены в кэше!")
        print(f"Найдена команда 1: {team1_found}")
        print(f"Найдена команда 2: {team2_found}")
        
        # В будущем здесь будет запуск генерации изображения
        
        self.main_window.toggle_generate_button(True)


    @Slot(str)
    def on_post_type_changed(self, post_type: str):
        """
        Обработчик сигнала `post_type_changed`.
        """
        print(f"Тип поста изменен на: {post_type}")
        self.main_window.set_status_message(f"Выбран режим '{post_type}'")

    @Slot()
    def on_team_input_started(self):
        """
        Обработчик сигнала `team_input_started`.
        """
        print("Пользователь начал вводить название команды.")
        self.main_window.set_status_message("Готово к поиску...")