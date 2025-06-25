# core/image_generator.py
import os
import traceback
from PIL import Image, ImageDraw, ImageFont
from config import OUTPUT_DIR, LOGO_DIR, IMAGE_SIZE, DEFAULT_BACKGROUND_COLOR_1
from core.models import Team # Импортируем для аннотаций типов

# --- НАДЕЖНОЕ ОПРЕДЕЛЕНИЕ ПУТИ К ШРИФТАМ ---
# Это гарантирует, что программа найдет шрифты, где бы вы ее ни запустили
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    # Запасной вариант, если __file__ не определен (например, в интерактивной среде)
    BASE_DIR = os.path.abspath('.')

# Пути к разным начертаниям шрифта
FONT_MEDIUM_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'onest-medium.ttf')
FONT_BOLD_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'onest-bold.ttf')


class ImageGenerator:
    """
    Отвечает за создание итогового изображения для поста.
    Использует ИСКЛЮЧИТЕЛЬНО библиотеку Pillow.
    """
    def __init__(self):
        self.fonts = {}
        try:
            # Загружаем все нужные шрифты и размеры один раз
            self.fonts['league'] = ImageFont.truetype(FONT_MEDIUM_PATH, size=45)
            self.fonts['team_name'] = ImageFont.truetype(FONT_BOLD_PATH, size=40)
            self.fonts['form'] = ImageFont.truetype(FONT_MEDIUM_PATH, size=35)
            self.fonts['prediction'] = ImageFont.truetype(FONT_BOLD_PATH, size=60)
            self.fonts['stats_header'] = ImageFont.truetype(FONT_MEDIUM_PATH, size=38)
            self.fonts['stats_value'] = ImageFont.truetype(FONT_BOLD_PATH, size=38)
            print("Шрифты успешно загружены.")
        except IOError as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить шрифт. Убедитесь, что файлы существуют: {FONT_MEDIUM_PATH} и {FONT_BOLD_PATH}. Ошибка: {e}")
            # В случае сбоя, все шрифты будут стандартными
            self.fonts = {key: ImageFont.load_default() for key in ['league', 'team_name', 'form', 'prediction', 'stats_header', 'stats_value']}
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print("ImageGenerator инициализирован. Рендеринг только через Pillow.")

    def _draw_text(self, draw, text, position, font, fill=(255, 255, 255), anchor='ms'):
        """Вспомогательная функция для отрисовки текста с якорем."""
        draw.text(position, text, font=font, fill=fill, anchor=anchor)

    def create_single_post_image(self, team1: Team, stats1: dict, team2: Team, stats2: dict, prediction: str) -> str | None:
        try:
            background = Image.new('RGB', IMAGE_SIZE, color=DEFAULT_BACKGROUND_COLOR_1)
            draw = ImageDraw.Draw(background)

            # --- Шапка: Название лиги ---
            league_name = stats1.get('league', {}).get('name', 'Лига не указана')
            self._draw_text(draw, league_name.upper(), (IMAGE_SIZE[0] // 2, 80), self.fonts['league'])

            # --- Логотипы ---
            logo1 = Image.open(os.path.join(LOGO_DIR, team1.logo_filename)).convert("RGBA")
            logo2 = Image.open(os.path.join(LOGO_DIR, team2.logo_filename)).convert("RGBA")

            logo_size = (300, 300)
            logo1_resized = logo1.resize(logo_size, Image.Resampling.LANCZOS)
            logo2_resized = logo2.resize(logo_size, Image.Resampling.LANCZOS)

            pos1_logo = (250, 250)
            pos2_logo = (IMAGE_SIZE[0] - logo_size[0] - 250, 250)
            background.paste(logo1_resized, pos1_logo, logo1_resized)
            background.paste(logo2_resized, pos2_logo, logo2_resized)
            
            # --- Названия и форма команд ---
            self._draw_text(draw, team1.name, (pos1_logo[0] + logo_size[0]//2, 580), self.fonts['team_name'])
            form1 = stats1.get('form', '?????')[-5:]
            self._draw_text(draw, f"Форма: {form1}", (pos1_logo[0] + logo_size[0]//2, 640), self.fonts['form'], fill=(200, 200, 200))

            self._draw_text(draw, team2.name, (pos2_logo[0] + logo_size[0]//2, 580), self.fonts['team_name'])
            form2 = stats2.get('form', '?????')[-5:]
            self._draw_text(draw, f"Форма: {form2}", (pos2_logo[0] + logo_size[0]//2, 640), self.fonts['form'], fill=(200, 200, 200))

            # --- Прогноз ---
            self._draw_text(draw, prediction, (IMAGE_SIZE[0] // 2, 750), self.fonts['prediction'])

            # --- Статистика ---
            stats_y_start, line_height = 880, 60
            center_x, col1_x, col3_x = IMAGE_SIZE[0] // 2, 450, IMAGE_SIZE[0] - 450
            stats_map = {"Победы": ('fixtures', 'wins'), "Ничьи": ('fixtures', 'draws'), "Поражения": ('fixtures', 'loses'), "Средний гол": ('goals', 'average')}

            for i, (label, keys) in enumerate(stats_map.items()):
                y = stats_y_start + i * line_height
                self._draw_text(draw, label, (center_x, y), self.fonts['stats_header'], fill=(200, 200, 200), anchor='mm')
                stat1_val = stats1.get(keys[0], {}).get(keys[1], {}).get('total', '-')
                self._draw_text(draw, str(stat1_val), (col1_x, y), self.fonts['stats_value'], anchor='rm')
                stat2_val = stats2.get(keys[0], {}).get(keys[1], {}).get('total', '-')
                self._draw_text(draw, str(stat2_val), (col3_x, y), self.fonts['stats_value'], anchor='lm')

            # --- Сохранение ---
            output_filename = f"{team1.name}_vs_{team2.name}_final.png"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            background.save(output_path, 'PNG')
            
            print(f"Изображение успешно создано (Pillow): {output_path}")
            return output_path
            
        except FileNotFoundError as e:
            print(f"ОШИБКА: Файл не найден. Скорее всего, неверный путь к логотипу. {e}\n{traceback.format_exc()}")
            return None
        except Exception as e:
            print(f"Произошла непредвиденная ошибка при создании изображения: {e}\n{traceback.format_exc()}")
            return None