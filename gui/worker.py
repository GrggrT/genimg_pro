# gui/worker.py

from PySide6.QtCore import QObject, Signal, Slot

class Worker(QObject):
    """
    Асинхронный обработчик для выполнения длительных задач в отдельном потоке.

    Сигналы:
        finished(object): Испускается при успешном завершении задачи.
                          Передает результат выполнения функции.
        error(Exception): Испускается, если во время выполнения произошло исключение.
                          Передает объект исключения.
        progress(str):    Испускается для обновления статуса в основном потоке.
                          Передает текстовое сообщение.
    """
    finished = Signal(object)
    error = Signal(Exception)
    progress = Signal(str)

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
        try:
            # Передаем сигнал progress в качестве аргумента,
            # если целевая функция его поддерживает.
            # Это позволяет сообщать о прогрессе изнутри выполняемой задачи.
            if 'worker_progress_signal' in self.func.__code__.co_varnames:
                self.kwargs['worker_progress_signal'] = self.progress
            
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)