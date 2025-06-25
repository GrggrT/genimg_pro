# core/api_clients.py

import requests
import httpx  # Добавляем импорт для асинхронных запросов
import asyncio # Добавляем для демонстрационного запуска
from typing import Optional, Dict, Any

# Предполагается, что эти переменные существуют в вашем config.py
from config import APIFOOTBALL_KEY

# --- Базовый класс для всех API клиентов ---
class BaseApiClient:
    """Абстрактный базовый класс для API клиентов."""
    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Этот метод должен быть переопределен в дочернем классе.")

# --- РЕАЛИЗАЦИЯ ДЛЯ API-FOOTBALL ---
class ApiFootballClient(BaseApiClient):
    """Клиент для взаимодействия с API-Football (v3)."""
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

    def __init__(self, api_key: Optional[str] = APIFOOTBALL_KEY):
        if not api_key:
            raise ValueError("Ключ для API-Football не предоставлен. Проверьте .env файл.")
        self.headers = {
            'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
            'x-rapidapi-key': api_key
        }

    # --- Существующий синхронный метод ---
    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Ищет команду по имени через API-Football (v3).
        """
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
                
            team_info = data["response"][0]["team"]
            result = {
                "id": team_info.get("id"), # Добавим ID, он понадобится для статистики
                "name": team_info.get("name"),
                "logo_url": team_info.get("logo")
            }
            print(f"API-FOOTBALL (v3): Найдена команда '{result['name']}' с ID {result['id']}")
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
    
    # --- НОВЫЙ АСИНХРОННЫЙ МЕТОД ---
    async def fetch_team_statistics(self, team_id: int, league_id: int, season: int) -> Optional[Dict[str, Any]]:
        """
        Асинхронно получает полную статистику команды для указанной лиги и сезона.
        """
        endpoint = f"{self.BASE_URL}/teams/statistics"
        params = {
            "team": str(team_id),
            "league": str(league_id),
            "season": str(season)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"API-FOOTBALL (async): Запрос статистики для team_id={team_id}, league_id={league_id}...")
                response = await client.get(endpoint, headers=self.headers, params=params, timeout=15.0)
                response.raise_for_status()
                data = response.json()
                
                if data and data.get("results", 0) > 0 and "response" in data:
                    print(f"API-FOOTBALL (async): Статистика для team_id={team_id} успешно получена.")
                    return data["response"]
                else:
                    print(f"API-FOOTBALL (async): Статистика не найдена для team_id={team_id}, league_id={league_id}, season={season}.")
                    return None
            except httpx.TimeoutException:
                print(f"API-FOOTBALL (async): Ошибка: Превышено время ожидания ответа.")
                return None
            except httpx.HTTPStatusError as e:
                print(f"API-FOOTBALL (async): HTTP ошибка при запросе статистики: {e.response.status_code} - {e.response.text}")
                return None
            except httpx.RequestError as e:
                print(f"API-FOOTBALL (async): Ошибка сети или соединения при запросе статистики: {e}")
                return None

# --- Пример использования (для демонстрации) ---
async def demo_main():
    print("--- Демонстрация работы ApiFootballClient ---\n")
    
    if not APIFOOTBALL_KEY:
        print("Ключ APIFOOTBALL_KEY не найден. Демонстрация невозможна.")
        return

    client = ApiFootballClient(api_key=APIFOOTBALL_KEY)
    
    # 1. Сначала найдем команду синхронно, чтобы получить ее ID
    print("--- Шаг 1: Поиск ID команды (синхронно) ---")
    team_data = client.fetch_team_data("Man Utd")
    
    if not team_data:
        print("\nНе удалось найти команду. Демонстрация статистики невозможна.")
        return
        
    # 2. Теперь используем ID для асинхронного получения статистики
    print("\n--- Шаг 2: Запрос статистики (асинхронно) ---")
    team_id, league_id, season = team_data['id'], 39, 2020 # ID, Premier League, Season 2020
    
    statistics = await client.fetch_team_statistics(team_id=team_id, league_id=league_id, season=season)
    
    if statistics:
        print("\n--- Успешно получена статистика ---")
        print(f"Команда: {statistics.get('team', {}).get('name')}")
        print(f"Лига: {statistics.get('league', {}).get('name')}")
        print(f"Форма: {statistics.get('form', 'N/A')}")
        print("---------------------------------")
    else:
        print("\n--- Не удалось получить статистику ---")

if __name__ == '__main__':
    # Для запуска асинхронного демонстрационного кода
    asyncio.run(demo_main())