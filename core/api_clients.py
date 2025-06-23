# core/api_clients.py
import requests
import os
from typing import Optional, Dict, Any

from config import APIFOOTBALL_KEY, LOGO_DIR

# --- Вспомогательная функция для загрузки изображений ---
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
        print(f"API_CLIENT: URL логотипа для '{team_name}' пуст.")
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

        print(f"API_CLIENT: Логотип для '{team_name}' успешно скачан и сохранен как '{logo_path}'")
        return logo_path

    except requests.exceptions.RequestException as e:
        print(f"API_CLIENT: Ошибка при скачивании логотипа для '{team_name}': {e}")
        return None


# --- Базовый класс для всех API клиентов ---
class BaseApiClient:
    """Абстрактный базовый класс для API клиентов."""
    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Этот метод должен быть переопределен в дочернем классе.")


# --- Реализация для API-Football ---
class ApiFootballClient(BaseApiClient):
    """Клиент для взаимодействия с API-Football."""
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: Optional[str] = APIFOOTBALL_KEY):
        if not api_key:
            raise ValueError("Ключ для API-Football не предоставлен. Проверьте .env файл.")
        self.headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': api_key
        }

    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Ищет команду по имени через API-Football.

        Args:
            team_name (str): Имя команды для поиска.

        Returns:
            Словарь с данными команды {'name': str, 'logo_url': str} или None.
        """
        endpoint = f"{self.BASE_URL}/teams"
        params = {"search": team_name}
        
        try:
            print(f"API-FOOTBALL: Поиск команды '{team_name}'...")
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data["results"]:
                print(f"API-FOOTBALL: Команда '{team_name}' не найдена.")
                return None
                
            # Берем наиболее релевантный результат (первый в списке)
            team_info = data["response"][0]["team"]
            result = {
                "name": team_info["name"],
                "logo_url": team_info["logo"]
            }
            print(f"API-FOOTBALL: Найдена команда '{result['name']}'")
            return result

        except requests.exceptions.Timeout:
            print(f"API-FOOTBALL: Ошибка: Превышено время ожидания ответа от сервера.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"API-FOOTBALL: HTTP ошибка при запросе: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"API-FOOTBALL: Ошибка сети или соединения: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"API-FOOTBALL: Ошибка при разборе ответа от API: {e}")
            return None