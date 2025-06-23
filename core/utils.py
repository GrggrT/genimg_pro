# core/utils.py
import os
import requests
from typing import Optional
from config import LOGO_DIR

def download_logo(team_name: str, logo_url: str) -> Optional[str]:
    """
    Загружает логотип по URL и сохраняет его в директорию кэша.

    Args:
        team_name (str): Имя команды, используется для создания имени файла.
        logo_url (str): URL для скачивания логотипа.

    Returns:
        Optional[str]: Путь к сохраненному файлу или None в случае ошибки.
    """
    if not logo_url:
        print(f"UTILS: URL логотипа для '{team_name}' пуст.")
        return None

    try:
        response = requests.get(logo_url, stream=True, timeout=10)
        response.raise_for_status() # Проверка на HTTP ошибки (4xx или 5xx)

        # Создаем безопасное имя файла
        safe_filename = "".join(c for c in team_name if c.isalnum() or c in (' ', '_')).rstrip()
        logo_filename = f"{safe_filename}.png"
        logo_path = os.path.join(LOGO_DIR, logo_filename)

        # Создаем директорию, если она не существует
        os.makedirs(LOGO_DIR, exist_ok=True)

        with open(logo_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"UTILS: Логотип для '{team_name}' успешно скачан и сохранен как '{logo_path}'")
        return logo_path

    except requests.exceptions.RequestException as e:
        print(f"UTILS: Ошибка при скачивании логотипа для '{team_name}': {e}")
        return None