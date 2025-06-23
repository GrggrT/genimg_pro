# gui/main_window.py
import sys
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QPixmap
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
    save_image_requested = Signal(str) # Сигнал для сохранения файла
    clear_clicked = Signal() # Сигнал для сброса состояния

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GenImg Pro v2.0")
        self.setGeometry(100, 100, 800, 850) # Увеличим высоту окна

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
        
        # --- НОВОЕ: Прогресс-бар ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False) # Скрыт по-умолчанию
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Готово")
        main_layout.addWidget(self.progress_bar)

        # --- Секция для предпросмотра изображения ---
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout()
        self.image_preview_label = QLabel("Здесь появится сгенерированное изображение")
        self.image_preview_label.setMinimumHeight(300)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setScaledContents(True)
        preview_layout.addWidget(self.image_preview_label)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # --- Кнопка генерации ---
        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.setFixedHeight(40)
        main_layout.addWidget(self.generate_button)

        # --- НОВОЕ: Кнопки управления ---
        controls_layout = QHBoxLayout()
        self.save_as_button = QPushButton("Сохранить как...")
        self.clear_button = QPushButton("Очистить")
        
        self.save_as_button.setEnabled(False) # Кнопка неактивна до генерации
        
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
        if self.radio_single.isChecked():
            self.post_type_changed.emit("single")
        else:
            self.post_type_changed.emit("express")
            
    def _on_save_as_clicked(self):
        """Открывает диалог сохранения файла и отправляет сигнал с путем."""
        # Открываем диалог сохранения файла
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            "", # Начальная директория
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)"
        )
        if path:
            self.save_image_requested.emit(path)

    # --- Слоты для управления из ViewModel ---
    @Slot(str)
    def display_image(self, path: str):
        pixmap = QPixmap(path)
        self.image_preview_label.setPixmap(pixmap)
        self.save_as_button.setEnabled(True) # Активируем кнопку сохранения
        self.set_status_message(f"Изображение успешно сгенерировано: {path}")

    @Slot(int, str)
    def update_progress(self, value: int, text: str):
        """Обновляет состояние прогресс-бара."""
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(text)

    @Slot()
    def clear_all_fields(self):
        """Очищает все поля ввода и предпросмотр."""
        self.team1_input.clear()
        self.team2_input.clear()
        self.prediction_input.clear()
        self.image_preview_label.setText("Здесь появится сгенерированное изображение")
        self.image_preview_label.setPixmap(QPixmap()) # Очищаем картинку
        self.save_as_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Готово")
        self.clear_clicked.emit() # Сообщаем ViewModel, что все очищено

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
    sys.exit(app.exec())
```

### Git-комментарий к изменениям:

```
feat(gui): Добавлен расширенный контроль и обратная связь

- **QProgressBar**: В интерфейс интегрирован прогресс-бар.
  - Добавлен слот `update_progress(value, text)` для обновления его состояния из ViewModel.
  - Прогресс-бар скрыт по умолчанию и появляется во время выполнения задач.

- **Кнопка "Сохранить как..."**:
  - Добавлена кнопка для сохранения сгенерированного изображения.
  - При нажатии открывается системный диалог `QFileDialog`.
  - Отправляет сигнал `save_image_requested(path)` с выбранным путем в ViewModel.
  - Кнопка становится активной только после успешной генерации изображения.

- **Кнопка "Очистить"**:
  - Добавлена кнопка для сброса всех полей ввода и области предпросмотра.
  - Реализован слот `clear_all_fields()`, который также отправляет сигнал `clear_clicked` в ViewModel для сброса внутреннего состояния.

Эти улучшения делают приложение значительно более удобным и интерактивным для конечного пользователя.
```

Я полностью обновил `gui/main_window.py`, реализовав все ваши пожелания. Теперь пользовательский интерфейс стал более информативным и функциональн