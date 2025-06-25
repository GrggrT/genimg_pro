# core/image_generator.py
import os
from PIL import Image, ImageDraw, ImageFont
from config import (
    OUTPUT_DIR, LOGO_DIR, IMAGE_SIZE,
    DEFAULT_BACKGROUND_COLOR_1, FONT_PATH
)

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
        
        # --- Загрузка шрифтов разных размеров ---
        try:
            self.font_league = ImageFont.truetype(FONT_PATH, size=45)
            self.font_team = ImageFont.truetype(FONT_PATH, size=40)
            self.font_form = ImageFont.truetype(FONT_PATH, size=35)
            self.font_prediction = ImageFont.truetype(FONT_PATH, size=60)
            self.font_stats_header = ImageFont.truetype(FONT_PATH, size=38)
            self.font_stats_value = ImageFont.truetype(FONT_PATH, size=38)
            print("Шрифты успешно загружены.")
        except IOError:
            print(f"Шрифт не найден по пути: {FONT_PATH}. Используется шрифт по умолчанию.")
            # В случае ошибки, загружаем шрифты по умолчанию
            self.font_league = self.font_team = self.font_form = self.font_prediction \
            = self.font_stats_header = self.font_stats_value = ImageFont.load_default()

    def _draw_text(self, draw, position, text, font, fill=(255, 255, 255), anchor="ms"):
        """Вспомогательная функция для отрисовки текста с центрированием."""
        draw.text(position, text, font=font, fill=fill, anchor=anchor)

    def create_single_post_image(self, team1_data: dict, team1_stats: dict, team2_data: dict, team2_stats: dict, prediction_text: str) -> str | None:
        """
        Создает информационное изображение для одиночного поста.

        Args:
            team1_data (dict): Данные команды 1.
            team1_stats (dict): Статистика команды 1.
            team2_data (dict): Данные команды 2.
            team2_stats (dict): Статистика команды 2.
            prediction_text (str): Текст прогноза.

        Returns:
            str | None: Путь к сохраненному файлу или None в случае ошибки.
        """
        try:
            # 1. Создание холста
            background = Image.new('RGB', IMAGE_SIZE, color=DEFAULT_BACKGROUND_COLOR_1)
            draw = ImageDraw.Draw(background)

            # --- 2. Шапка: Название лиги ---
            league_name = team1_stats.get('league', {}).get('name', 'Лига не указана')
            self._draw_text(draw, (IMAGE_SIZE[0] // 2, 80), league_name.upper(), self.font_league)

            # --- 3. Центральная зона: Логотипы и названия команд ---
            logo1_path = os.path.join(LOGO_DIR, team1_data['logo_filename'])
            logo2_path = os.path.join(LOGO_DIR, team2_data['logo_filename'])

            logo1 = Image.open(logo1_path).convert("RGBA")
            logo2 = Image.open(logo2_path).convert("RGBA")

            logo_size = (300, 300)
            logo1 = logo1.resize(logo_size, Image.Resampling.LANCZOS)
            logo2 = logo2.resize(logo_size, Image.Resampling.LANCZOS)

            pos1 = (250, 250)
            pos2 = (IMAGE_SIZE[0] - logo_size[0] - 250, 250)
            background.paste(logo1, pos1, logo1)
            background.paste(logo2, pos2, logo2)
            
            self._draw_text(draw, (pos1[0] + logo_size[0]//2, 580), team1_data['name'], self.font_team)
            self._draw_text(draw, (pos2[0] + logo_size[0]//2, 580), team2_data['name'], self.font_team)

            # --- 4. Зона "Форма" ---
            form1 = team1_stats.get('form', '?????')[-5:]
            form2 = team2_stats.get('form', '?????')[-5:]
            self._draw_text(draw, (pos1[0] + logo_size[0]//2, 640), f"Форма: {form1}", self.font_form, fill=(200, 200, 200))
            self._draw_text(draw, (pos2[0] + logo_size[0]//2, 640), f"Форма: {form2}", self.font_form, fill=(200, 200, 200))

            # --- 5. Ваш прогноз ---
            self._draw_text(draw, (IMAGE_SIZE[0] // 2, 750), prediction_text, self.font_prediction)

            # --- 6. Нижняя зона (статистика) ---
            stats_y_start = 900
            line_height = 60
            center_x = IMAGE_SIZE[0] // 2
            col1_x = 350
            col3_x = IMAGE_SIZE[0] - 350

            stats_map = {
                "Победы": ('fixtures', 'wins'),
                "Ничьи": ('fixtures', 'draws'),
                "Поражения": ('fixtures', 'loses'),
                "Средний гол": ('goals', 'average')
            }
            
            for i, (label, keys) in enumerate(stats_map.items()):
                y = stats_y_start + i * line_height
                
                # Статистика команды 1
                stat1_val = team1_stats.get(keys[0], {}).get(keys[1], {}).get('total', '-')
                self._draw_text(draw, (col1_x, y), str(stat1_val), self.font_stats_value, anchor="ms")
                
                # Название показателя
                self._draw_text(draw, (center_x, y), label, self.font_stats_header, fill=(200, 200, 200), anchor="mm")

                # Статистика команды 2
                stat2_val = team2_stats.get(keys[0], {}).get(keys[1], {}).get('total', '-')
                self._draw_text(draw, (col3_x, y), str(stat2_val), self.font_stats_value, anchor="ms")

            # --- 7. Сохранение ---
            safe_name1 = "".join(c for c in team1_data['name'] if c.isalnum())
            safe_name2 = "".join(c for c in team2_data['name'] if c.isalnum())
            output_filename = f"{safe_name1}_vs_{safe_name2}_stats.png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            background.save(output_path, 'PNG', quality=95)
            print(f"Изображение-дашборд успешно создано: {output_path}")
            
            return output_path

        except FileNotFoundError as e:
            print(f"Ошибка: Не найден файл логотипа. {e}")
            return None
        except Exception as e:
            print(f"Произошла непредвиденная ошибка при создании изображения: {e}")
            return None