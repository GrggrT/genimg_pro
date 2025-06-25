# gui/main_window.py
import sys
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QPixmap, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStatusBar,
    QFormLayout,
    QGroupBox,
    QRadioButton,
    QMessageBox,
    QProgressBar,
    QFileDialog
)

class MainWindow(QMainWindow):
    """
    Главное окно приложения GenImg Pro (View).
    """
    # --- Сигналы для ViewModel ---
    generate_clicked = Signal()
    post_type_changed = Signal(str)
    team_input_started = Signal(str)
    save_image_requested = Signal(str)
    clear_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GenImg Pro v2.0")
        self.setGeometry(100, 100, 800, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ... (секции выбора типа поста и ввода данных без изменений) ...
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
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Готово")
        main_layout.addWidget(self.progress_bar)

        # --- ОБНОВЛЕНО: Секция для предпросмотра изображения ---
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout()
        self.image_preview_label = QLabel("Здесь появится сгенерированное изображение")
        self.image_preview_label.setAlignment(Qt.AlignCenter) # Выравнивание по центру
        self.image_preview_label.setMinimumSize(400, 400) # Минимальный размер
        preview_layout.addWidget(self.image_preview_label)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # ... (кнопки и статус-бар без изменений) ...
        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.setFixedHeight(40)
        main_layout.addWidget(self.generate_button)

        controls_layout = QHBoxLayout()
        self.save_as_button = QPushButton("Сохранить как...")
        self.clear_button = QPushButton("Очистить")
        self.save_as_button.setEnabled(False)
        controls_layout.addWidget(self.save_as_button)
        controls_layout.addWidget(self.clear_button)
        main_layout.addLayout(controls_layout)

        main_layout.addStretch()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # --- Привязка сигналов ---
        self.generate_button.clicked.connect(self.generate_clicked)
        self.radio_single.toggled.connect(self._on_post_type_changed)
        self.team1_input.textChanged.connect(self.team_input_started)
        self.team2_input.textChanged.connect(self.team_input_started)
        self.save_as_button.clicked.connect(self._on_save_as_clicked)
        self.clear_button.clicked.connect(self.clear_all_fields)

    def _on_post_type_changed(self):
        # ... (без изменений) ...
        if self.radio_single.isChecked():
            self.post_type_changed.emit("single")
        else:
            self.post_type_changed.emit("express")
            
    def _on_save_as_clicked(self):
        # ... (без изменений) ...
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)")
        if path:
            self.save_image_requested.emit(path)

    # --- ОБНОВЛЕНО: Слот для отображения изображения ---
    @Slot(str)
    def display_image(self, image_path: str):
        """Отображает сгенерированное изображение в QLabel."""
        if not image_path:
            self.image_preview_label.setText("Не удалось сгенерировать изображение.")
            self.save_as_button.setEnabled(False)
            return
        
        pixmap = QPixmap(image_path)
        # Масштабируем изображение под размер QLabel с сохранением пропорций
        self.image_preview_label.setPixmap(pixmap.scaled(
            self.image_preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        self.save_as_button.setEnabled(True)
        self.set_status_message(f"Изображение успешно отображено: {image_path}")


    @Slot(int, str)
    def update_progress(self, value: int, text: str):
        # ... (без изменений) ...
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(text)

    @Slot()
    def clear_all_fields(self):
        # ... (без изменений) ...
        self.team1_input.clear()
        self.team2_input.clear()
        self.prediction_input.clear()
        self.image_preview_label.setText("Здесь появится сгенерированное изображение")
        self.image_preview_label.setPixmap(QPixmap())
        self.save_as_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Готово")
        self.clear_clicked.emit()

    @Slot(str)
    def set_status_message(self, message: str):
        # ... (без изменений) ...
        self.status_bar.showMessage(message)

    @Slot(bool)
    def toggle_generate_button(self, enabled: bool):
        # ... (без изменений) ...
        self.generate_button.setEnabled(enabled)

    @Slot(str, str)
    def show_error_message(self, title: str, message: str):
        # ... (без изменений) ...
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event: QCloseEvent):
        # ... (без изменений) ...
        print("Окно закрывается, приложение завершает работу.")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```
### Git-комментарий к изменениям:

```
feat(gui): Улучшено отображение изображений в MainWindow

- **gui/main_window.py**:
  - Обновлен слот `display_image(path)` для более качественного отображения. Теперь изображение масштабируется под размер виджета с сохранением пропорций (`Qt.KeepAspectRatio`).
  - Добавлена проверка на случай, если путь к изображению не был передан.
  - Установлен минимальный размер для `image_preview_label` и выравнивание по центру для лучшего визуального представления.
  - Импортированы `QPixmap` и `Qt` для работы с изображениями и константами.
