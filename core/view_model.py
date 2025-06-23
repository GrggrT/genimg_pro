# core/view_model.py

import requests
import os
from PySide6.QtCore import QObject, Slot
from gui.main_window import MainWindow
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient  # Предполагаем, что класс находится здесь
from config import LOGO_DIR # Импортируем путь для сохранения логотипов

class ViewModel(QObject):
    """
    ViewModel соединяет View (GUI) и Model (логику).
    """
    def __init__(self, main_window: MainWindow, cache_manager: CacheManager, api_client: ApiFootballClient):
        """
        Инициализирует ViewModel.

        :param main_window: Экземпляр главного окна (View).
        :param cache_manager: Экземпляр менеджера кэша (Model).
        :param api_client: Экземпляр API-клиента для получения данных из сети.
        """
        super().__init__()
        self.main_window = main_window
        self.cache_manager = cache_manager
        self.api_client = api_client

        # --- Соединение сигналов из View со слотами в ViewModel ---
        self.main_window.generate_clicked.connect(self.on_generate_clicked)
        self.main_window.post_type_changed.connect(self.on_post_type_changed)
        self.main_window.team_input_started.connect(self.on_team_input_started)

    def _download_logo(self, logo_url: str, team_name: str) -> str | None:
        """
        Вспомогательная функция для загрузки логотипа по URL.
        Возвращает путь к файлу в случае успеха или None в случае ошибки.
        """
        try:
            response = requests.get(logo_url, stream=True, timeout=10)
            response.raise_for_status() # Проверка на HTTP-ошибки

            # Создаем безопасное имя файла
            safe_filename = "".join(c for c in team_name if c.isalnum() or c in (' ', '_')).rstrip()
            logo_filename = f"{safe_filename}.png"
            logo_path = os.path.join(LOGO_DIR, logo_filename)

            # Создаем директорию, если ее нет
            os.makedirs(LOGO_DIR, exist_ok=True)

            with open(logo_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Логотип для '{team_name}' успешно скачан и сохранен как '{logo_path}'")
            return logo_path
        except requests.RequestException as e:
            print(f"Ошибка при загрузке логотипа для '{team_name}': {e}")
            self.main_window.set_status_message(f"Ошибка сети при загрузке логотипа для {team_name}.")
            return None


    @Slot()
    def on_generate_clicked(self):
        """
        Основная логика обработки нажатия на кнопку "Сгенерировать".
        """
        self.main_window.toggle_generate_button(False)
        self.main_window.set_status_message("Проверка введенных данных...")

        team1_name = self.main_window.team1_input.text().strip()
        team2_name = self.main_window.team2_input.text().strip()

        if not team1_name or not team2_name:
            self.main_window.set_status_message("Ошибка: Названия обеих команд должны быть заполнены.")
            self.main_window.toggle_generate_button(True)
            return

        teams_to_find = {
            "Команда 1": team1_name,
            "Команда 2": team2_name
        }
        
        found_teams_data = {}

        for key, team_name in teams_to_find.items():
            self.main_window.set_status_message(f"Поиск '{team_name}' в локальном кэше...")
            team_data = self.cache_manager.find_team_by_name(team_name)

            if team_data:
                print(f"Команда '{team_name}' найдена в кэше.")
                found_teams_data[key] = team_data
                continue

            # --- Логика "Промаха кэша" ---
            self.main_window.set_status_message(f"'{team_name}' не найдена в кэше. Ищу в интернете...")
            api_data = self.api_client.fetch_team_data(team_name)

            if not api_data or not api_data.get('logo_url'):
                self.main_window.set_status_message(f"Ошибка: Команда '{team_name}' не найдена ни в кэше, ни через API.")
                self.main_window.toggle_generate_button(True)
                return

            # --- Загрузка логотипа ---
            self.main_window.set_status_message(f"Загружаю логотип для '{team_name}'...")
            logo_path = self._download_logo(api_data['logo_url'], api_data['name'])

            if not logo_path:
                self.main_window.set_status_message(f"Не удалось загрузить логотип для '{team_name}'.")
                self.main_window.toggle_generate_button(True)
                return
            
            # --- Добавление в кэш ---
            self.main_window.set_status_message(f"Сохраняю '{team_name}' в кэш...")
            self.cache_manager.add_team_to_cache(
                name=api_data['name'],
                logo_path=os.path.basename(logo_path), # Сохраняем только имя файла
                api_source='api-football', # или другой источник
                aliases=[team_name] # Добавляем исходный запрос как псевдоним
            )
            
            # Повторный поиск в кэше, чтобы получить полный объект
            found_teams_data[key] = self.cache_manager.find_team_by_name(team_name)

        # --- Финальная проверка и завершение ---
        if len(found_teams_data) == 2:
            self.main_window.set_status_message("Все команды успешно найдены и готовы к генерации!")
            print("Данные для генерации:")
            print(f"Команда 1: {found_teams_data['Команда 1']}")
            print(f"Команда 2: {found_teams_data['Команда 2']}")
        else:
             self.main_window.set_status_message("Произошла непредвиденная ошибка при поиске команд.")

        self.main_window.toggle_generate_button(True)


    @Slot(str)
    def on_post_type_changed(self, post_type: str):
        self.main_window.set_status_message(f"Выбран режим '{post_type}'")

    @Slot()
    def on_team_input_started(self):
        self.main_window.set_status_message("Готово к поиску...")