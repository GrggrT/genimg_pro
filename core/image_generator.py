# core/image_generator.py
import os
from PIL import Image, ImageDraw, ImageFont
from config import OUTPUT_DIR, LOGO_DIR, IMAGE_SIZE, DEFAULT_BACKGROUND_COLOR_1, FONT_PATH
# Убедитесь, что здесь НЕТ импортов из PySide6

class ImageGenerator:
    """
    Отвечает за создание итогового изображения для поста.
    Использует ИСКЛЮЧИТЕЛЬНО библиотеку Pillow.
    """
    def __init__(self):
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            print(f"Создана директория для сгенерированных изображений: {OUTPUT_DIR}")

    # Тип данных для team_data может быть как объектом, так и словарем,
    # поэтому для универсальности обращаемся к атрибутам через getattr()
    def create_single_post_image(self, team1_data, team2_data, prediction_text: str) -> str | None:
        """
        Создает изображение для одиночного поста.

        Args:
            team1_data (Team): ОБЪЕКТ первой команды из SQLAlchemy.
            team2_data (Team): ОБЪЕКТ второй команды из SQLAlchemy.
            prediction_text (str): Текст прогноза для размещения на изображении.

        Returns:
            str | None: Путь к сохраненному файлу изображения или None в случае ошибки.
        """
        try:
            # 1. Загрузка фонового шаблона
            background = Image.new('RGB', IMAGE_SIZE, color=DEFAULT_BACKGROUND_COLOR_1)
            draw = ImageDraw.Draw(background)

            # 2. Загрузка логотипов команд
            logo1_path = os.path.join(LOGO_DIR, getattr(team1_data, 'logo_filename', ''))
            logo2_path = os.path.join(LOGO_DIR, getattr(team2_data, 'logo_filename', ''))

            logo1 = Image.open(logo1_path).convert("RGBA")
            logo2 = Image.open(logo2_path).convert("RGBA")

            logo_size = (300, 300)
            logo1 = logo1.resize(logo_size, Image.Resampling.LANCZOS)
            logo2 = logo2.resize(logo_size, Image.Resampling.LANCZOS)

            # 3. Размещение логотипов
            pos1 = (150, (IMAGE_SIZE[1] - logo_size[1]) // 2)
            pos2 = (IMAGE_SIZE[0] - logo_size[0] - 150, (IMAGE_SIZE[1] - logo_size[1]) // 2)

            background.paste(logo1, pos1, logo1)
            background.paste(logo2, pos2, logo2)

            # 4. Добавление текста прогноза
            try:
                font = ImageFont.truetype(FONT_PATH, size=60)
            except IOError:
                print(f"Шрифт не найден по пути: {FONT_PATH}. Используется шрифт по умолчанию.")
                font = ImageFont.load_default()

            text_bbox = draw.textbbox((0, 0), prediction_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_pos = ((IMAGE_SIZE[0] - text_width) // 2, 950)
            draw.text(text_pos, prediction_text, font=font, fill=(255, 255, 255))

            # 5. Сохранение готового изображения
            team1_name = getattr(team1_data, 'name', 'Team1')
            team2_name = getattr(team2_data, 'name', 'Team2')
            output_filename = f"{team1_name}_vs_{team2_name}.png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            background.save(output_path, 'PNG', quality=95)
            print(f"Изображение успешно создано и сохранено: {output_path}")

            return output_path

        except FileNotFoundError as e:
            print(f"Ошибка: Не найден файл логотипа. {e}")
            return None
        except Exception as e:
            print(f"Произошла ошибка при создании изображения: {e}")
            return None