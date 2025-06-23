# core/api_clients.py
import requests
from typing import Optional, Dict, Any

from config import APIFOOTBALL_KEY
# Импортируем общую функцию из нового модуля утилит
from core.utils import download_logo

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