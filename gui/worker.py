# gui/worker.py
from PySide6.QtCore import QObject, Signal, Slot, QThread

class Worker(QObject):
    """
    Асинхронный обработчик для выполнения длительных задач в отдельном потоке.
    """
    finished = Signal(object)
    error = Signal(Exception)
    progress = Signal(int, str) # Изменен для передачи (value, text)

    def __init__(self, func, *args, **kwargs):
        """
        :param func: Функция, которую необходимо выполнить.
        :param args: Позиционные аргументы для функции.
        :param kwargs: Именованные аргументы для функции.
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        """
        Выполняет задачу и испускает соответствующий сигнал.
        """
        # <<< ДОБАВЛЕНО ДЛЯ ДИАГНОСТИКИ >>>
        print(f"[DEBUG] Worker запущен в потоке: {QThread.currentThread().objectName()} ({QThread.currentThreadId()})")
        
        try:
            # Проверяем, может ли функция принять сигнал прогресса
            # и передаем его, если это возможно.
            if 'worker_progress_signal' in self.func.__code__.co_varnames:
                self.kwargs['worker_progress_signal'] = self.progress
            
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            # Выводим ошибку в консоль для отладки
            import traceback
            print(f"[ERROR] В Worker произошла ошибка:")
            traceback.print_exc()
            self.error.emit(e)

