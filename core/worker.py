# core/worker.py
import sys
import traceback
from PySide6.QtCore import QObject, Signal, Slot

class Worker(QObject):
    """
    Универсальный обработчик для выполнения длительных задач в фоновом потоке.

    Сигналы:
        finished(result): Испускается при успешном завершении задачи.
        error(message): Испускается, если во время выполнения задачи произошло исключение.
        progress(percent): Испускается для информирования о прогрессе выполнения.
    """
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, target_func, *args, **kwargs):
        """
        Инициализирует Worker.

        :param target_func: Функция, которую необходимо выполнить.
        :param args: Позиционные аргументы для target_func.
        :param kwargs: Именованные аргументы для target_func.
        """
        super().__init__()
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        """
        Выполняет задачу и обрабатывает возможные исключения.
        """
        try:
            # Выполняем переданную функцию
            result = self.target_func(*self.args, **self.kwargs)
        except Exception as e:
            # В случае ошибки формируем сообщение и испускаем сигнал error
            ex_type, ex_value, ex_traceback = sys.exc_info()
            error_msg = f"Произошла ошибка: {e}\n"
            error_msg += "".join(traceback.format_tb(ex_traceback))
            self.error.emit(error_msg)
        else:
            # Если все прошло успешно, испускаем сигнал finished с результатом
            self.finished.emit(result)