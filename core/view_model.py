# core/view_model.py

import os
import requests
from PySide6.QtCore import QObject, Slot, QThread
from gui.main_window import MainWindow
from gui.worker import Worker
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient
from core.image_generator import ImageGenerator
from config import LOGO_DIR

class ViewModel(QObject):
    """
    Асинхронный ViewModel, управляющий логикой приложения без блокировки GUI.
    """
    def __init__(self, main_window: MainWindow, cache_manager: CacheManager,
                 api_client: ApiFootballClient, image_generator: ImageGenerator):
        super().__init__()
        self.main_window = main_window
        self.cache_manager = cache_manager
        self.api_client = api_client
        self.image_generator = image_generator

        # --- Состояние для асинхронного потока ---
        self.thread = None
        self.worker = None
        self.team1_data = None
        self.team2_data = None

        # --- Подключение сигналов ---
        self.main_window.generate_clicked.connect(self.on_generate_clicked)
        # ... (другие сигналы)

    def _run_task(self, func, *args, on_finish, **kwargs):
        """Запускает задачу в отдельном потоке."""
        self.thread = QThread()
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        # Соединяем сигналы
        self.worker.progress.connect(self.main_window.set_status_message)
        self.worker.error.connect(self._on_task_error)
        self.worker.finished.connect(on_finish)
        self.thread.started.connect(self.worker.run)
        
        # Очистка после завершения
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _find_team_flow(self, team_name: str, worker_progress_signal: Signal = None):
        """
        Логика поиска команды (кэш -> api -> загрузка).
        Эта функция будет выполняться в отдельном потоке.
        """
        def report_progress(msg):
            if worker_progress_signal:
                worker_progress_signal.emit(msg)

        report_progress(f"Поиск '{team_name}' в кэше...")
        team_data = self.cache_manager.find_team_by_name(team_name)
        if team_data:
            return team_data

        report_progress(f"'{team_name}' не найдена в кэше. Ищу в интернете...")
        api_data = self.api_client.fetch_team_data(team_name)
        if not api_data or not api_data.get('logo_url'):
            raise ValueError(f"Команда '{team_name}' не найдена нигде.")

        report_progress(f"Загружаю логотип для '{api_data['name']}'...")
        logo_path = self._download_logo(api_data['logo_url'], api_data['name'])
        if not logo_path:
            raise ConnectionError(f"Не удалось загрузить логотип для '{api_data['name']}'.")

        report_progress(f"Сохраняю '{api_data['name']}' в кэш...")
        self.cache_manager.add_team_to_cache(
            name=api_data['name'], logo_path=os.path.basename(logo_path),
            api_source='api-football', aliases=[team_name]
        )
        return self.cache_manager.find_team_by_name(team_name)

    @Slot()
    def on_generate_clicked(self):
        """
        Запускает асинхронную цепочку поиска данных и генерации изображения.
        """
        self.main_window.toggle_generate_button(False)
        self.team1_data = None
        self.team2_data = None
        
        team1_name = self.main_window.team1_input.text().strip()
        self._run_task(self._find_team_flow, team1_name, on_finish=self._on_team1_found)

    @Slot(object)
    def _on_team1_found(self, team1_result):
        """Обработчик успешного поиска первой команды."""
        self.team1_data = team1_result
        team2_name = self.main_window.team2_input.text().strip()
        self._run_task(self._find_team_flow, team2_name, on_finish=self._on_team2_found)

    @Slot(object)
    def _on_team2_found(self, team2_result):
        """Обработчик успешного поиска второй команды."""
        self.team2_data = team2_result
        prediction_text = self.main_window.prediction_input.text()
        
        self._run_task(
            self.image_generator.create_single_post_image,
            self.team1_data, self.team2_data, prediction_text,
            on_finish=self._on_generation_finished
        )

    @Slot(object)
    def _on_generation_finished(self, image_path):
        """Обработчик успешного создания изображения."""
        self.main_window.set_status_message(f"Изображение успешно сохранено: {image_path}")
        self.main_window.toggle_generate_button(True)

    @Slot(Exception)
    def _on_task_error(self, e):
        """Обработчик любой ошибки в асинхронной цепочке."""
        print(f"Произошла ошибка: {e}")
        self.main_window.set_status_message(f"Ошибка: {e}")
        self.main_window.toggle_generate_button(True)

    def _download_logo(self, logo_url: str, team_name: str) -> str | None:
        # Эта функция остается такой же, как и раньше, т.к. она вызывается
        # изнутри _find_team_flow, который уже работает в отдельном потоке.
        try:
            response = requests.get(logo_url, stream=True, timeout=10)
            response.raise_for_status()
            safe_filename = "".join(c for c in team_name if c.isalnum() or c in (' ', '_')).rstrip()
            logo_filename = f"{safe_filename}.png"
            logo_path = os.path.join(LOGO_DIR, logo_filename)
            os.makedirs(LOGO_DIR, exist_ok=True)
            with open(logo_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return logo_path
        except requests.RequestException as exc:
            raise ConnectionError(f"Ошибка сети при загрузке логотипа: {exc}") from exc