# core/view_model.py
import os
import requests
from PySide6.QtCore import QObject, Slot, QThread, Signal
from gui.main_window import MainWindow
from gui.worker import Worker
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient
from core.image_generator import ImageGenerator
from config import LOGO_DIR
from typing import Optional, Dict, Any, Callable

class ViewModel(QObject):
    """
    Асинхронный ViewModel, управляющий логикой приложения без блокировки GUI.
    """
    def __init__(self, main_window: MainWindow, cache_manager: CacheManager,
                 api_client: ApiFootballClient, image_generator: ImageGenerator) -> None:
        """
        Инициализирует ViewModel.
        """
        super().__init__()
        self.main_window = main_window
        self.cache_manager = cache_manager
        self.api_client = api_client
        self.image_generator = image_generator

        # <<< ИЗМЕНЕНИЕ: Инициализируем атрибут для хранения потока >>>
        self.thread: Optional[QThread] = None
        
        self.worker: Optional[Worker] = None
        self.team1_data: Optional[Dict[str, Any]] = None
        self.team2_data: Optional[Dict[str, Any]] = None

        self.main_window.generate_clicked.connect(self.on_generate_clicked)

    def _run_task(self, func: Callable, *args: Any, on_finish: Callable) -> None:
        """
        Универсальный метод для запуска задачи в отдельном потоке.
        """
        # <<< ИЗМЕНЕНИЕ: Сохраняем ссылку на созданный поток >>>
        self.thread = QThread()
        self.worker = Worker(func, *args)
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(self.main_window.set_status_message)
        self.worker.error.connect(self._on_task_error)
        self.worker.finished.connect(on_finish)
        
        self.thread.started.connect(self.worker.run)
        
        # Связываем сигнал finished потока с его удалением, чтобы избежать утечек памяти
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # При успешном завершении обнуляем ссылку на поток
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))

        self.thread.start()

    # ... (остальные методы, такие как _find_team_flow, on_generate_clicked и т.д., остаются без изменений) ...
    def _find_team_flow(self, team_name: str, worker_progress_signal: Optional[Signal] = None) -> Dict[str, Any]:
        """
        Полный цикл поиска команды: кэш -> API -> загрузка -> кэширование.
        """
        def report_progress(msg):
            if worker_progress_signal:
                worker_progress_signal.emit(msg)

        report_progress(f"Поиск '{team_name}' в кэше...")
        team_data = self.cache_manager.find_team_by_alias(team_name)
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
        self.cache_manager.add_or_update_team(
            team_name=api_data['name'],
            logo_filename=os.path.basename(logo_path),
            api_source='api-football',
            aliases=[team_name, api_data['name']]
        )
        return self.cache_manager.find_team_by_alias(team_name)

    @Slot()
    def on_generate_clicked(self):
        """
        Запускает асинхронную цепочку поиска данных и генерации изображения.
        """
        if self.thread and self.thread.isRunning():
            print("Операция уже выполняется.")
            return

        self.main_window.toggle_generate_button(False)
        self.team1_data = None
        self.team2_data = None
        
        team1_name = self.main_window.team1_input.text().strip()
        self._run_task(self._find_team_flow, team1_name, on_finish=self._on_team1_found)

    @Slot(object)
    def _on_team1_found(self, team1_result):
        self.team1_data = team1_result
        team2_name = self.main_window.team2_input.text().strip()
        self._run_task(self._find_team_flow, team2_name, on_finish=self._on_team2_found)

    @Slot(object)
    def _on_team2_found(self, team2_result):
        self.team2_data = team2_result
        prediction_text = self.main_window.prediction_input.text()
        self._run_task(
            self.image_generator.create_single_post_image,
            self.team1_data, self.team2_data, prediction_text,
            on_finish=self._on_generation_finished
        )

    @Slot(object)
    def _on_generation_finished(self, image_path):
        self.main_window.set_status_message(f"Изображение успешно сохранено: {image_path}")
        self.main_window.toggle_generate_button(True)

    @Slot(Exception)
    def _on_task_error(self, e):
        print(f"Произошла ошибка: {e}")
        self.main_window.set_status_message(f"Ошибка: {e}")
        self.main_window.toggle_generate_button(True)
        # Обнуляем ссылку на поток при ошибке
        if self.thread:
             self.thread.quit()
             self.thread = None

    def _download_logo(self, logo_url: str, team_name: str) -> str:
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

    # >>> НОВЫЙ МЕТОД ДЛЯ КОРРЕКТНОЙ ОСТАНОВКИ <<<
    def shutdown(self):
        """Корректно останавливает рабочий поток перед выходом."""
        if self.thread and self.thread.isRunning():
            print("Запрос на остановку фонового потока...")
            self.thread.quit()  # Посылаем сигнал "завершайся"
            self.thread.wait()  # Ожидаем, пока поток действительно не завершится
            print("Фоновый поток успешно остановлен.")