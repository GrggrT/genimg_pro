# core/image_generator.py
import os
from PIL import Image, ImageDraw, ImageFont
from config import OUTPUT_DIR, LOGO_DIR, IMAGE_SIZE, DEFAULT_BACKGROUND_COLOR_1, FONT_PATH

class ImageGenerator:
    """
    Отвечает за создание итогового изображения для поста.
    """

    def __init__(self):
        """
        Инициализирует генератор изображений.
        Создает выходную директорию, если она не существует.
        """
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            print(f"Создана директория для сгенерированных изображений: {OUTPUT_DIR}")

    def create_single_post_image(self, team1_data: dict, team2_data: dict, prediction_text: str) -> str | None:
        """
        Создает изображение для одиночного поста.

        Args:
            team1_data (dict): Словарь с данными первой команды, включая 'name' и 'logo_filename'.
            team2_data (dict): Словарь с данными второй команды, включая 'name' и 'logo_filename'.
            prediction_text (str): Текст прогноза для размещения на изображении.

        Returns:
            str | None: Путь к сохраненному файлу изображения или None в случае ошибки.
        """
        try:
            # 1. Загрузка фонового шаблона (простой цветной фон)
            background = Image.new('RGB', IMAGE_SIZE, color=DEFAULT_BACKGROUND_COLOR_1)
            draw = ImageDraw.Draw(background)

            # 2. Загрузка логотипов команд
            logo1_path = os.path.join(LOGO_DIR, team1_data['logo_filename'])
            logo2_path = os.path.join(LOGO_DIR, team2_data['logo_filename'])

            logo1 = Image.open(logo1_path).convert("RGBA")
            logo2 = Image.open(logo2_path).convert("RGBA")

            # Изменяем размер логотипов для размещения
            logo_size = (300, 300)
            logo1 = logo1.resize(logo_size, Image.Resampling.LANCZOS)
            logo2 = logo2.resize(logo_size, Image.Resampling.LANCZOS)

            # 3. Размещение (накладывание) логотипов на фон
            # Размещаем логотипы по бокам, оставляя центр для текста
            pos1 = (150, (IMAGE_SIZE[1] - logo_size[1]) // 2)
            pos2 = (IMAGE_SIZE[0] - logo_size[0] - 150, (IMAGE_SIZE[1] - logo_size[1]) // 2)

            background.paste(logo1, pos1, logo1)
            background.paste(logo2, pos2, logo2)

            # 4. Добавление текста прогноза
            try:
                # Используем шрифт из конфига, если он доступен
                font = ImageFont.truetype(FONT_PATH, size=60)
            except IOError:
                print(f"Шрифт не найден по пути: {FONT_PATH}. Используется шрифт по умолчанию.")
                font = ImageFont.load_default()
                
            text_bbox = draw.textbbox((0, 0), prediction_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            text_pos = ((IMAGE_SIZE[0] - text_width) // 2, 950)
            draw.text(text_pos, prediction_text, font=font, fill=(255, 255, 255))

            # 5. Сохранение готового изображения
            output_filename = f"{team1_data['name']}_vs_{team2_data['name']}.png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            background.save(output_path, 'PNG', quality=95)
            print(f"Изображение успешно создано и сохранено: {output_path}")

            # 6. Возвращение пути к файлу
            return output_path

        except FileNotFoundError as e:
            print(f"Ошибка: Не найден файл логотипа. {e}")
            return None
        except Exception as e:
            print(f"Произошла ошибка при создании изображения: {e}")
            return None

if __name__ == '__main__':
    # Пример использования (для тестирования)
    # Убедитесь, что у вас есть папка logos_cache с нужными файлами
    # и настроен config.py
    
    # Создаем фейковые данные для теста
    if not os.path.exists(LOGO_DIR):
        os.makedirs(LOGO_DIR)
        
    # Создадим фейковые логотипы, если их нет
    try:
        Image.new('RGB', (100, 100), color = 'red').save(os.path.join(LOGO_DIR, "Team A.png"))
        Image.new('RGB', (100, 100), color = 'blue').save(os.path.join(LOGO_DIR, "Team B.png"))
    except Exception as e:
        print(f"Не удалось создать тестовые логотипы: {e}")


    team1_test_data = {'name': 'Team A', 'logo_filename': 'Team A.png'}
    team2_test_data = {'name': 'Team B', 'logo_filename': 'Team B.png'}
    prediction = "П1 с форой (-1.5)"

    generator = ImageGenerator()
    image_path = generator.create_single_post_image(team1_test_data, team2_test_data, prediction)

    if image_path:
        print(f"\nТестовое изображение доступно по пути: {image_path}")