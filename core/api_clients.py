# core/api_clients.py

import requests
from typing import Optional, Dict, Any
from config import APIFOOTBALL_KEY, LOGO_DIR
from core.utils import download_logo # Используем утилиту

# --- Базовый класс для всех API клиентов ---
class BaseApiClient:
    """Абстрактный базовый класс для API клиентов."""
    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Этот метод должен быть переопределен в дочернем классе.")

# --- РЕАЛИЗАЦИЯ ДЛЯ API-FOOTBALL ---
class ApiFootballClient(BaseApiClient):
    """Клиент для взаимодействия с API-Football (v3)."""
    # !!! ВАЖНЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ !!!
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3" # URL для v3, как в вашем curl

    def __init__(self, api_key: Optional[str] = APIFOOTBALL_KEY):
        if not api_key:
            raise ValueError("Ключ для API-Football не предоставлен. Проверьте .env файл.")
        self.headers = {
            # !!! ВАЖНЫЕ ИЗМЕНЕНИЯ ЗДЕСЬ !!!
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com", # Хост, как в вашем curl
            'x-rapidapi-key': api_key
        }

    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Ищет команду по имени через API-Football (v3).
        """
        # Эндпоинт для поиска команд в v3
        endpoint = f"{self.BASE_URL}/teams"
        params = {"search": team_name}
        
        try:
            print(f"API-FOOTBALL (v3): Поиск команды '{team_name}'...")
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("results") or not data.get("response"):
                print(f"API-FOOTBALL (v3): Команда '{team_name}' не найдена.")
                return None
                
            # Берем наиболее релевантный результат (первый в списке)
            team_info = data["response"][0]["team"]
            result = {
                "name": team_info.get("name"),
                "logo_url": team_info.get("logo")
            }
            print(f"API-FOOTBALL (v3): Найдена команда '{result['name']}'")
            return result

        except requests.exceptions.Timeout:
            print(f"API-FOOTBALL (v3): Ошибка: Превышено время ожидания ответа от сервера.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"API-FOOTBALL (v3): HTTP ошибка при запросе: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"API-FOOTBALL (v3): Ошибка сети или соединения: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"API-FOOTBALL (v3): Ошибка при разборе ответа от API: {e}, Ответ: {data}")
            return None