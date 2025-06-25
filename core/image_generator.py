# core/image_generator.py
import os
from PySide6.QtGui import QPainter, QImage, QFont, QFontDatabase, QColor, QPen
from PySide6.QtCore import QRectF, Qt

# Предполагается, что эти переменные определены в вашем config.py
# Пример:
# TEMPLATE_PATH = "assets/template.png"
# FONTS_DIR = "assets/fonts"
# OUTPUT_DIR = "output"
# LOGO_DIR = "logos_cache"
from config import OUTPUT_DIR, LOGO_DIR

# Предполагается, что у вас есть такая модель
# (если нет, можно снова использовать словари)
from core.models import Team 

class ImageGenerator:
    """
    Класс для создания изображений на основе данных о командах и прогнозов,
    используя PySide6 (Qt) для рендеринга.
    """
    def __init__(self):
        """Инициализирует генератор, загружает шрифты и проверяет пути."""
        self.template_path = TEMPLATE_PATH
        self.fonts = {}
        self._load_fonts()
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print("ImageGenerator инициализирован. Используется рендеринг через Qt.")

    def _load_fonts(self):
        """Загружает кастомные шрифты из директории assets/fonts."""
        if not os.path.exists(FONTS_DIR):
            print(f"ВНИМАНИЕ: Директория со шрифтами не найдена: {FONTS_DIR}")
            return
            
        for font_file in os.listdir(FONTS_DIR):
            if font_file.lower().endswith('.ttf'):
                font_path = os.path.join(FONTS_DIR, font_file)
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    # Ключ - имя файла без расширения
                    font_name = os.path.splitext(font_file)[0]
                    self.fonts[font_name] = font_family
        if self.fonts:
            print(f"Шрифты успешно загружены: {list(self.fonts.keys())}")
        else:
            print("Кастомные шрифты не загружены. Будет использован шрифт по умолчанию.")

    def _get_font(self, name: str, size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
        """Вспомогательный метод для получения настроенного объекта QFont."""
        font_family = self.fonts.get(name, 'Arial') # Arial как запасной вариант
        font = QFont(font_family, size)
        font.setWeight(weight)
        return font

    def create_single_post_image(self, team1_data: Team, team1_stats: dict, team2_data: Team, team2_stats: dict, prediction_text: str) -> str:
        """
        Создает информационное изображение для поста, используя QPainter.
        """
        image = QImage(self.template_path)
        
        # --- ВАША ПРОВЕРКА ---
        # Проверяем, загрузился ли шаблон, перед тем как начать рисовать.
        if image.isNull():
            raise FileNotFoundError(f"Критическая ошибка: Не удалось загрузить шаблон изображения по пути: {self.template_path}")

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        white_color = QColor('white')
        gray_color = QColor('#A9A9A9') # Тусклый серый для доп. информации

        # 1. Шапка: Название лиги
        league_name = team1_stats.get('league', {}).get('name', 'Лига не указана')
        painter.setFont(self._get_font('onest-medium', 45))
        painter.setPen(white_color)
        painter.drawText(QRectF(0, 50, image.width(), 60), Qt.AlignmentFlag.AlignCenter, league_name.upper())

        # 2. Логотипы
        logo1_path = os.path.join(LOGO_DIR, os.path.basename(team1_data.logo_path))
        logo2_path = os.path.join(LOGO_DIR, os.path.basename(team2_data.logo_path))
        logo1 = QImage(logo1_path)
        logo2 = QImage(logo2_path)
        
        if not logo1.isNull():
            painter.drawImage(QRectF(250, 250, 300, 300), logo1)
        if not logo2.isNull():
            painter.drawImage(QRectF(image.width() - 550, 250, 300, 300), logo2)
        
        # 3. Названия команд
        painter.setFont(self._get_font('onest-bold', 40, QFont.Weight.Bold))
        painter.setPen(white_color)
        painter.drawText(QRectF(150, 580, 500, 50), Qt.AlignmentFlag.AlignCenter, team1_data.name)
        painter.drawText(QRectF(image.width() - 650, 580, 500, 50), Qt.AlignmentFlag.AlignCenter, team2_data.name)

        # 4. Форма команд
        form1 = team1_stats.get('form', '?????')[-5:]
        form2 = team2_stats.get('form', '?????')[-5:]
        painter.setFont(self._get_font('onest-regular', 35))
        painter.setPen(gray_color)
        painter.drawText(QRectF(150, 640, 500, 40), Qt.AlignmentFlag.AlignCenter, f"Форма: {form1}")
        painter.drawText(QRectF(image.width() - 650, 640, 500, 40), Qt.AlignmentFlag.AlignCenter, f"Форма: {form2}")

        # 5. Прогноз
        painter.setFont(self._get_font('onest-bold', 60, QFont.Weight.Bold))
        painter.setPen(white_color)
        painter.drawText(QRectF(0, 740, image.width(), 70), Qt.AlignmentFlag.AlignCenter, prediction_text)
        
        # 6. Статистика
        stats_y_start = 880
        line_height = 60
        stats_map = {
            "Победы": ('fixtures', 'wins'), "Ничьи": ('fixtures', 'draws'),
            "Поражения": ('fixtures', 'loses'), "Средний гол": ('goals', 'average')
        }
        
        for i, (label, keys) in enumerate(stats_map.items()):
            y = stats_y_start + i * line_height
            stat1_val = team1_stats.get(keys[0], {}).get(keys[1], {}).get('total', '-')
            stat2_val = team2_stats.get(keys[0], {}).get(keys[1], {}).get('total', '-')
            
            # Название метрики
            painter.setFont(self._get_font('onest-medium', 38))
            painter.setPen(gray_color)
            painter.drawText(QRectF(0, y, image.width(), 50), Qt.AlignmentFlag.AlignCenter, label)

            # Значения
            painter.setFont(self._get_font('onest-bold', 38, QFont.Weight.Bold))
            painter.setPen(white_color)
            painter.drawText(QRectF(350, y, 200, 50), Qt.AlignmentFlag.AlignLeft, str(stat1_val))
            painter.drawText(QRectF(image.width() - 550, y, 200, 50), Qt.AlignmentFlag.AlignRight, str(stat2_val))

        painter.end()

        # Сохранение файла
        safe_name1 = "".join(c for c in team1_data.name if c.isalnum())
        safe_name2 = "".join(c for c in team2_data.name if c.isalnum())
        output_filename = f"{safe_name1}_vs_{safe_name2}_qt.png"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        if image.save(output_path):
            print(f"Изображение успешно сохранено: {output_path}")
        else:
            print(f"Ошибка: Не удалось сохранить изображение в {output_path}")

        return output_path