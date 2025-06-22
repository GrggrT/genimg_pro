# gui/main_window.py
import sys
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
    QRadioButton
)

class MainWindow(QMainWindow):
    """
    Главное окно приложения GenImg Pro.

    Отвечает за отображение пользовательского интерфейса (View).
    Вся логика управления состоянием и обработки событий
    будет делегироваться в ViewModel.
    """
    def __init__(self, parent=None):
        """
        Инициализирует главное окно и его компоненты.
        """
        super().__init__(parent)

        # --- Базовые настройки окна ---
        self.setWindowTitle("GenImg Pro v2.0")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        # --- Создание центрального виджета и основного макета ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 1. Секция выбора типа поста ---
        post_type_group = QGroupBox("Тип поста")
        post_type_layout = QVBoxLayout()
        self.radio_single = QRadioButton("Одиночный")
        self.radio_express = QRadioButton("Экспресс")
        self.radio_single.setChecked(True) # По умолчанию выбран "Одиночный"
        post_type_layout.addWidget(self.radio_single)
        post_type_layout.addWidget(self.radio_express)
        post_type_group.setLayout(post_type_layout)
        main_layout.addWidget(post_type_group)

        # --- 2. Секция ввода данных ---
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

        # --- 3. Кнопка генерации ---
        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.setFixedHeight(40) # Делаем кнопку более заметной
        main_layout.addWidget(self.generate_button)

        # --- Добавляем растягивающийся элемент для выравнивания ---
        main_layout.addStretch()

        # --- 4. Статус-бар для уведомлений ---
        # В соответствии с пунктом 3.2.3 Технического Задания
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")


if __name__ == '__main__':
    # Этот блок для тестирования и предпросмотра окна
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())