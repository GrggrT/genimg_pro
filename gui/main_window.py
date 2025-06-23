# gui/main_window.py
import sys
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QPixmap
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
    """
    generate_clicked = Signal()
    post_type_changed = Signal(str)
    team_input_started = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GenImg Pro v2.0")
        self.setGeometry(100, 100, 800, 750) # Увеличим высоту окна

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ... (код для выбора типа поста и ввода данных остается без изменений) ...
        post_type_group = QGroupBox("Тип поста")
        post_type_layout = QVBoxLayout()
        self.radio_single = QRadioButton("Одиночный")
        self.radio_express = QRadioButton("Экспресс")
        self.radio_single.setChecked(True)
        post_type_layout.addWidget(self.radio_single)
        post_type_layout.addWidget(self.radio_express)
        post_type_group.setLayout(post_type_layout)
        main_layout.addWidget(post_type_group)

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

        # --- НОВОЕ: Секция для предпросмотра изображения ---
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout()
        self.image_preview_label = QLabel("Здесь появится сгенерированное изображение")
        self.image_preview_label.setMinimumHeight(300) # Задаем минимальную высоту
        self.image_preview_label.setScaledContents(True) # Масштабируем содержимое
        preview_layout.addWidget(self.image_preview_label)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # --- Кнопка генерации ---
        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.setFixedHeight(40)
        main_layout.addWidget(self.generate_button)

        main_layout.addStretch()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # --- Привязка сигналов ---
        self.generate_button.clicked.connect(self.generate_clicked)
        self.radio_single.toggled.connect(self._on_post_type_changed)
        self.radio_express.toggled.connect(self._on_post_type_changed)
        self.team1_input.textChanged.connect(self.team_input_started)
        self.team2_input.textChanged.connect(self.team_input_started)

    def _on_post_type_changed(self):
        if self.radio_single.isChecked():
            self.post_type_changed.emit("single")
        else:
            self.post_type_changed.emit("express")

    # --- НОВЫЙ СЛОТ: для отображения изображения ---
    @Slot(str)
    def display_image(self, path: str):
        """Загружает изображение из файла и отображает его в image_preview_label."""
        pixmap = QPixmap(path)
        self.image_preview_label.setPixmap(pixmap)
        self.set_status_message(f"Изображение успешно сгенерировано: {path}")

    @Slot(str)
    def set_status_message(self, message: str):
        self.status_bar.showMessage(message)

    @Slot(bool)
    def toggle_generate_button(self, enabled: bool):
        self.generate_button.setEnabled(enabled)

    @Slot(str, str)
    def show_error_message(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Пример вызова нового слота (для теста нужно иметь файл 'test.png')
    # window.display_image('test.png')
    sys.exit(app.exec())
```

### 2. Финальное обновление `main.py`

Теперь я обновлю главный файл, чтобы он создавал и передавал `ImageGenerator` в `ViewModel`.


```python
# main.py
import sys
from PySide6.QtWidgets import QApplication

# Импортируем наши компоненты
from gui.main_window import MainWindow
from core.view_model import ViewModel
from core.cache_manager import CacheManager
from core.api_clients import ApiFootballClient
from core.image_generator import ImageGenerator  # <-- Новый импорт

def main():
    """
    Главная точка входа в приложение GenImg Pro.
    """
    app = QApplication(sys.argv)

    # Инициализируем все компоненты-зависимости
    main_window = MainWindow()
    cache_manager = CacheManager()
    api_client = ApiFootballClient()
    image_generator = ImageGenerator()  # <-- Создаем экземпляр генератора

    # Создаем ViewModel и внедряем в него все зависимости.
    view_model = ViewModel(
        view=main_window,
        cache_manager=cache_manager,
        api_client=api_client,
        image_generator=image_generator  # <-- Передаем генератор в ViewModel
    )

    # Отображаем главный интерфейс
    main_window.show()

    # Запускаем цикл событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
