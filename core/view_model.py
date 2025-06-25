# core/view_model.py

import os
import traceback
import transliterate
from PySide6.QtCore import QObject, QThread, Signal, Slot

from gui.main_window import MainWindow
from gui.worker import Worker
from core.cache_manager import CacheManager
from core.api_clients import BaseApiClient
from core.image_generator import ImageGenerator
from core.models import Team

class ViewModel(QObject):
    image_generated = Signal(str)

    def __init__(self, main_window: MainWindow, cache_manager: CacheManager,
                 api_client: BaseApiClient, image_generator: ImageGenerator):
        super().__init__()
        self.main_window = main_window
        self.cache_manager = cache_manager
        self.api_client = api_client
        self.image_generator = image_generator
        self.thread = None
        self.found_teams = {}

        self.main_window.generate_clicked.connect(self.on_generate_clicked)
        self.main_window.post_type_changed.connect(self.on_post_type_changed)
        self.main_window.team_input_started.connect(self.on_team_input_started)
        self.main_window.clear_clicked.connect(self.on_clear_clicked)

    def _start_task(self, func, *args, on_finish):
        """Универсальный метод для запуска фоновой задачи."""
        self.thread = QThread()
        worker = Worker(func, *args)
        worker.moveToThread(self.thread)

        worker.finished.connect(on_finish)
        # !!! КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: СОЕДИНЯЕМ СИГНАЛ ОШИБКИ СО СЛОТОМ !!!
        worker.error.connect(self._on_task_error)

        worker.finished.connect(self.thread.quit)
        worker.finished.connect(worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.started.connect(worker.run)
        self.thread.start()

    @Slot(str)
    def _on_task_error(self, error_message: str):
        """
        Слот, который вызывается при любой ошибке в фоновом потоке.
        Показывает пользователю диалоговое окно.
        """
        print(f"[ОШИБКА] Обработана ошибка в ViewModel: {error_message}")
        # Извлекаем только последнюю, самую понятную строку ошибки для пользователя
        user_friendly_message = error_message.strip().splitlines()[-1]
        self.main_window.show_error_message("Ошибка", user_friendly_message)
        self.main_window.toggle_generate_button(True)
        self.main_window.progress_bar.setVisible(False)

    def _find_team_flow(self, team_name: str) -> Team:
        """Полноценный поток поиска команды: кэш -> API."""
        original_team_name = team_name
        
        # Попытка транслитерации
        try:
            if any(c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in team_name.lower()):
                team_name_translit = transliterate.translit(team_name, 'ru', reversed=True)
                print(f"[DEBUG] Попытка транслитерации: '{team_name}' -> '{team_name_translit}'")
                
                # Сначала ищем по транслиту
                team = self.cache_manager.find_team_by_alias(team_name_translit)
                if team: return team
        except transliterate.exceptions.LanguageNotFoundError:
            print("[ПРЕДУПРЕЖДЕНИЕ] Библиотека transliterate не смогла определить язык.")

        # Ищем по оригинальному названию в кэше
        team = self.cache_manager.find_team_by_alias(original_team_name)
        if team: return team

        # Если не нашли в кэше, идем в API
        api_data = self.api_client.fetch_team_data(team_name)
        if not api_data:
            raise ValueError(f"Команда '{original_team_name}' не найдена ни в кэше, ни через API.")

        logo_path = self.api_client.download_logo(api_data['logo_url'], api_data['name'])
        if not logo_path:
            raise ValueError(f"Не удалось скачать логотип для '{api_data['name']}'.")
        
        # Добавляем в кэш, используя и оригинальный запрос, и точное имя из API как псевдонимы
        self.cache_manager.add_or_update_team(
            team_name=api_data['name'],
            logo_filename=os.path.basename(logo_path),
            api_source='api-football',
            aliases=[original_team_name, api_data['name']]
        )
        return self.cache_manager.find_team_by_alias(original_team_name)

    @Slot()
    def on_generate_clicked(self):
        """
        Основная логика, запускающая весь процесс.
        """
        team1_name = self.main_window.team1_input.text().strip()
        team2_name = self.main_window.team2_input.text().strip()

        # !!! ВАЖНОЕ ИЗМЕНЕНИЕ !!!
        # Проверяем, что поля не пусты, ПЕРЕД тем, как запускать потоки.
        if not team1_name or not team2_name:
            # Если поля пусты, просто показываем сообщение в статус-баре
            # и ничего больше не делаем. Это предотвратит запуск и закрытие.
            self.main_window.set_status_message("Введите названия обеих команд")
            return
            
        # Если поля заполнены, запускаем сложный процесс
        self.main_window.toggle_generate_button(False)
        self.main_window.progress_bar.setVisible(True)
        self.main_window.progress_bar.setValue(10)
        self.found_teams.clear()

        print("[DEBUG] ViewModel: Запуск поиска для Команды 1")
        self._start_task(self._find_team_flow, team1_name, on_finish=self._on_team1_found)

    def _on_team1_found(self, team1):
        """Колбэк после нахождения первой команды."""
        if not team1: return
        self.found_teams['team1'] = team1
        self.main_window.progress_bar.setValue(40)
        
        team2_name = self.main_window.team2_input.text().strip()
        print("[DEBUG] ViewModel: Запуск поиска для Команды 2")
        self._start_task(self._find_team_flow, team2_name, on_finish=self._on_team2_found)

    def _on_team2_found(self, team2):
        """Колбэк после нахождения второй команды."""
        if not team2: return
        self.found_teams['team2'] = team2
        self.main_window.progress_bar.setValue(70)

        prediction = self.main_window.prediction_input.text()
        print("[DEBUG] ViewModel: Запуск генерации изображения")
        self._start_task(self.image_generator.create_single_post_image, 
                         self.found_teams['team1'], 
                         self.found_teams['team2'], 
                         prediction, 
                         on_finish=self._on_image_generated)

    def _on_image_generated(self, image_path):
        """Колбэк после генерации изображения."""
        if not image_path: return
        self.main_window.progress_bar.setValue(100)
        self.image_generated.emit(image_path)
        self.main_window.toggle_generate_button(True)
        self.main_window.set_status_message("Готово!")
        # Скрываем прогресс-бар через пару секунд для наглядности
        # (в реальном приложении можно убрать)
        # QTimer.singleShot(2000, lambda: self.main_window.progress_bar.setVisible(False))


    @Slot()
    def on_clear_clicked(self):
        """Очищает все поля ввода и предпросмотр."""
        self.main_window.team1_input.clear()
        self.main_window.team2_input.clear()
        self.main_window.prediction_input.clear()
        self.main_window.image_preview_label.clear()
        self.main_window.image_preview_label.setText("Здесь будет ваше изображение...")
        self.main_window.set_status_message("Готово")
        self.main_window.progress_bar.setVisible(False)

    @Slot(str)
    def on_post_type_changed(self, post_type: str):
        print(f"Тип поста изменен на: {post_type}")
        self.main_window.set_status_message(f"Выбран режим '{post_type}'")

    @Slot()
    def on_team_input_started(self):
        self.main_window.set_status_message("Готово к поиску...")

    def shutdown(self):
        if self.thread and self.thread.isRunning():
            print("Запрос на остановку фонового потока...")
            self.thread.quit()
            self.thread.wait()
            print("Фоновый поток успешно остановлен.")