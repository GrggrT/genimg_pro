# gui/worker.py
import sys
import traceback
from PySide6.QtCore import QObject, QThread, Signal, Slot

class Worker(QObject):
    """
    Универсальный обработчик для выполнения длительных задач в фоновом потоке.
    """
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, fn, *args, **kwargs):
        """
        :param fn: Функция, которую нужно выполнить.
        :param args: Позиционные аргументы для функции.
        :param kwargs: Именованные аргументы для функции.
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        """Запускает выполнение задачи."""
        try:
            # !!! ИЗМЕНЕНИЕ ЗДЕСЬ !!!
            # Заменяем ошибочный QThread.currentThreadId() на id(QThread.currentThread())
            print(f"[DEBUG] Worker запущен в потоке: {QThread.currentThread().objectName()} ({id(QThread.currentThread())})")
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            # В случае ошибки, формируем подробное сообщение
            error_message = f"Произошла ошибка: {e}\n{traceback.format_exc()}"
            self.error.emit(error_message)
        else:
            # Если всё прошло успешно, отправляем результат
            self.finished.emit(result)