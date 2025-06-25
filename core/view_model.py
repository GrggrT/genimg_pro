# core/view_model.py

import os
import transliterate
from PySide6.QtCore import QObject, QThread, Signal, Slot, QMetaObject, Qt
from typing import Optional, Dict, Any, Callable

from gui.main_window import MainWindow
from gui.worker import Worker
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient
from core.image_generator import ImageGenerator
from core.models import Team

# Константы для статистики
LEAGUE_ID = 39  # Premier League
SEASON = 2024   # Сезон

class ViewModel(QObject):
    """
    Асинхронный ViewModel, управляющий логикой приложения, используя
    единый фоновый поток для стабильности и производительности.
    """
    image_generated = Signal(str)

    def __init__(self, main_window: MainWindow, cache_manager: CacheManager,
                 api_client: ApiFootballClient, image_generator: ImageGenerator):
        super().__init__()
        self.main_window = main_window
        self.cache_manager = cache_manager
        self.api_client = api_client
        self.image_generator = image_generator

        # --- ИСПРАВЛЕНИЕ: Создаем один постоянный поток ---
        self.worker_thread = QThread(self)
        self.worker_thread.start()

        # Атрибуты для хранения состояния
        self.worker: Optional[Worker] = None
        self.found_teams: Dict[str, Team] = {}
        self.team_stats: Dict[str, dict] = {}

        self.main_window.generate_clicked.connect(self.on_generate_clicked)
        self.main_window.clear_clicked.connect(self.on_clear_clicked)

    # <<< ИСПРАВЛЕНИЕ: Сигнатура метода изменена для явного разделения аргументов >>>
    def _start_task(self, func: Callable, on_finish: Callable, *func_args: Any):
        """
        Запускает задачу в постоянном фоновом потоке.
        Колбэк on_finish и аргументы для целевой функции передаются раздельно.
        """
        if self.worker:
            self.main_window.set_status_message("Подождите, предыдущая операция еще не завершена.")
            return

        self.worker = Worker(func, *func_args)
        self.worker.moveToThread(self.worker_thread)

        # Правильное подключение сигналов
        self.worker.finished.connect(on_finish)
        self.worker.error.connect(self._on_task_error)
        
        # Очистка после завершения
        self.worker.finished.connect(lambda: setattr(self, 'worker', None))
        self.worker.error.connect(lambda: setattr(self, 'worker', None))
        # <<< ИСПРАВЛЕНИЕ: Используем `self.worker` для корректного удаления >>>
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)

        # Безопасный запуск задачи в потоке
        QMetaObject.invokeMethod(self.worker, 'run', Qt.QueuedConnection)

    @Slot(str)
    def _on_task_error(self, error_message: str):
        print(f"[ОШИБКА] Обработана ошибка в ViewModel: {error_message}")
        user_friendly_message = error_message.strip().splitlines()[-1]
        self.main_window.show_error_message("Ошибка", user_friendly_message)
        self.main_window.toggle_generate_button(True)
        self.worker = None # Сбрасываем worker при ошибке

    def _find_team_flow(self, team_name: str) -> Team | None:
        """Полный цикл поиска команды с предварительной транслитерацией."""
        original_team_name = team_name
        try:
            if any('а' <= c <= 'я' for c in team_name.lower()):
                team_name = transliterate.translit(team_name, 'ru', reversed=True)
        except Exception:
            pass # Игнорируем ошибку и используем оригинальное имя
        
        team = self.cache_manager.find_team_by_alias(team_name)
        if team: return team

        if team_name != original_team_name:
            team = self.cache_manager.find_team_by_alias(original_team_name)
            if team: return team

        api_team = self.api_client.fetch_team_data(team_name)
        if not api_team:
            raise ValueError(f"Команда '{original_team_name}' не найдена нигде.")

        logo_path = self.api_client.download_logo(api_team)
        if not logo_path:
            raise ConnectionError(f"Не удалось загрузить логотип для '{api_team.name}'.")

        self.cache_manager.add_or_update_team(
            team_name=api_team.name,
            logo_filename=os.path.basename(logo_path),
            api_source='api-football',
            aliases=[original_team_name, team_name, api_team.name]
        )
        return self.cache_manager.find_team_by_alias(api_team.name)


    @Slot()
    def on_generate_clicked(self):
        """Запускает полную цепочку сбора данных."""
        self.main_window.toggle_generate_button(False)
        self.found_teams = {}
        self.team_stats = {}
        team1_name = self.main_window.team1_input.text().strip()
        self._start_task(self._find_team_flow, self._on_team1_found, team1_name)

    def _on_team1_found(self, team1: Team):
        if not team1: return
        self.found_teams['team1'] = team1
        team2_name = self.main_window.team2_input.text().strip()
        self._start_task(self._find_team_flow, self._on_team2_found, team2_name)

    def _on_team2_found(self, team2: Team):
        if not team2: return
        self.found_teams['team2'] = team2
        # <<< ИСПРАВЛЕНИЕ: Правильно передаем аргументы в _start_task >>>
        self._start_task(
            self.api_client.fetch_team_statistics,
            self._on_team1_stats_found,
            self.found_teams['team1'].id, LEAGUE_ID, SEASON
        )

    def _on_team1_stats_found(self, stats1: dict):
        if not stats1:
            return self._on_task_error("Не удалось получить статистику для первой команды.")
        self.team_stats['team1'] = stats1
        self._start_task(
            self.api_client.fetch_team_statistics,
            self._on_team2_stats_found,
            self.found_teams['team2'].id, LEAGUE_ID, SEASON
        )

    def _on_team2_stats_found(self, stats2: dict):
        if not stats2:
            return self._on_task_error("Не удалось получить статистику для второй команды.")
        self.team_stats['team2'] = stats2
        prediction = self.main_window.prediction_input.text()
        self._start_task(
            self.image_generator.create_single_post_image,
            self._on_image_generated,
            self.found_teams['team1'], self.team_stats['team1'],
            self.found_teams['team2'], self.team_stats['team2'],
            prediction
        )

    def _on_image_generated(self, image_path: str):
        """Обработчик успешного создания изображения."""
        if image_path:
            self.main_window.set_status_message("Изображение успешно сохранено!")
            self.image_generated.emit(image_path)
        self.main_window.toggle_generate_button(True)

    @Slot()
    def on_clear_clicked(self):
        """Очищает поля ввода и сбрасывает состояние."""
        self.main_window.team1_input.clear()
        self.main_window.team2_input.clear()
        self.main_window.prediction_input.clear()
        self.found_teams = {}
        self.team_stats = {}
        self.main_window.set_status_message("Готово к работе.")

    def shutdown(self):
        """Корректно останавливает фоновый поток перед выходом."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(5000)