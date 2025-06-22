# gui/main_window.py
import sys
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStatusBar,
    QFormLayout,
    QGroupBox,
    QRadioButton,
    QMessageBox
)

class MainWindow(QMainWindow):
    """
    Главное окно приложения GenImg Pro (View).

    Отвечает за отображение UI и передачу действий пользователя
    в ViewModel через сигналы. Реагирует на команды от ViewModel
    через слоты.
    """
    # --- 1. Определение кастомных сигналов ---
    # Сигнал для кнопки "Сгенерировать"
    generate_clicked = Signal()
    # Сигнал для изменения типа поста
    post_type_changed = Signal(str)
    # Сигнал для начала ввода в полях команд
    team_input_started = Signal(str) # Передает текст поля

    def __init__(self, parent=None):
        """
        Инициализирует главное окно и его компоненты.
        """
        super().__init__(parent)

        # --- Базовые настройки окна ---
        self.setWindowTitle("GenImg Pro v2.0")
        self.setGeometry(100, 100, 800, 600)

        # --- Создание центрального виджета и основного макета ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Секция выбора типа поста ---
        post_type_group = QGroupBox("Тип поста")
        post_type_layout = QVBoxLayout()
        self.radio_single = QRadioButton("Одиночный")
        self.radio_express = QRadioButton("Экспресс")
        self.radio_single.setChecked(True)
        post_type_layout.addWidget(self.radio_single)
        post_type_layout.addWidget(self.radio_express)
        post_type_group.setLayout(post_type_layout)
        main_layout.addWidget(post_type_group)

        # --- Секция ввода данных ---
        data_input_group = QGroupBox("Ввод данных")
        form_layout = QFormLayout()

        self.team1_input = QLineEdit()
        self.team2_input = QLineEdit()
        self.prediction_input = QLineEdit()

        form_layout.addRow("Команда 1:", self.team1_input)
        form_layout.addRow("Команда 2:", self.team2_input)
        form_layout.addRow("Прогноз:", self.prediction_input)

        data_input_group.setLayout(form_layout)
        main_layout.addWidget(data_input_group)

        # --- Кнопка генерации ---
        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.setFixedHeight(40)
        main_layout.addWidget(self.generate_button)

        main_layout.addStretch()

        # --- Статус-бар ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # --- 2. Привязка виджетов к сигналам ---
        self.generate_button.clicked.connect(self.generate_clicked)
        self.radio_single.toggled.connect(self._on_post_type_changed)
        self.radio_express.toggled.connect(self._on_post_type_changed)
        self.team1_input.textChanged.connect(self.team_input_started)
        self.team2_input.textChanged.connect(self.team_input_started)


    def _on_post_type_changed(self):
        """Внутренний слот для обработки сигналов от радиокнопок."""
        if self.radio_single.isChecked():
            self.post_type_changed.emit("single")
        else:
            self.post_type_changed.emit("express")

    # --- 3. Определение слотов для реакции на команды ViewModel ---

    @Slot(str)
    def set_status_message(self, message: str):
        """Обновляет сообщение в статус-баре."""
        self.status_bar.showMessage(message)

    @Slot(bool)
    def toggle_generate_button(self, enabled: bool):
        """Включает или отключает кнопку 'Сгенерировать'."""
        self.generate_button.setEnabled(enabled)

    @Slot(str, str)
    def show_error_message(self, title: str, message: str):
        """Показывает диалоговое окно с сообщением об ошибке."""
        QMessageBox.critical(self, title, message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()

    # --- Тестовый код для проверки сигналов и слотов ---
    window.generate_clicked.connect(lambda: window.set_status_message("Нажата кнопка 'Сгенерировать'"))
    window.post_type_changed.connect(lambda p_type: window.set_status_message(f"Выбран тип поста: {p_type}"))
    window.team_input_started.connect(lambda text: print(f"Ввод команды: {text}"))

    # Проверка слотов
    window.toggle_generate_button(False) # Отключаем кнопку для теста
    # window.show_error_message("Тестовая ошибка", "Это сообщение для проверки слота.")

    window.show()
    sys.exit(app.exec())