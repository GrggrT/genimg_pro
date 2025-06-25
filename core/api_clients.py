# core/api_clients.py

import requests
import logging
from typing import Optional, Dict, Any

# Импортируем модель Team, чтобы возвращать объект
# (Предполагается, что файл core/models.py существует)
from core.models import Team 

# Получаем настроенный логгер. Использовать logging вместо print -
# это требование из вашего ТЗ (3.1.3. Централизованное логирование)
log = logging.getLogger(__name__)

class ApiClientError(Exception):
    """Кастомное исключение для явной обработки ошибок API в ViewModel."""
    pass

class ApiFootballClient:
    """
    Клиент для взаимодействия с API-Football.
    """
    def __init__(self, api_key: str):
        """
        Инициализирует API клиент.
        """
        if not api_key:
            raise ValueError("API-ключ для ApiFootballClient не предоставлен.")
            
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self.api_key
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Внутренний метод для выполнения и обработки HTTP-запросов.
        Уменьшает дублирование кода и централизует обработку ошибок.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            # Вызовет исключение для кодов 4xx/5xx
            response.raise_for_status() 
            return response.json()
        except requests.exceptions.Timeout as e:
            log.error(f"Ошибка таймаута при запросе к {url}: {e}")
            raise ApiClientError(f"Сервер не ответил вовремя.") from e
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP ошибка при запросе к {url}: {e.response.status_code} {e.response.text}")
            raise ApiClientError(f"Ошибка API: {e.response.status_code}") from e
        except requests.exceptions.RequestException as e:
            log.error(f"Сетевая ошибка при запросе к {url}: {e}")
            raise ApiClientError("Ошибка сети. Проверьте подключение к интернету.") from e

    def fetch_team_data(self, team_name: str) -> Optional[Team]:
        """
        Ищет данные команды по ее названию через API.

        Args:
            team_name (str): Название команды для поиска.

        Returns:
            Optional[Team]: Объект Team с данными, если команда найдена, иначе None.
        
        Raises:
            ApiClientError: В случае сетевых проблем или ошибок API.
        """
        log.info(f"Выполняю поиск команды '{team_name}' через API-Football...")
        
        data = self._make_request("teams", params={"search": team_name})

        if data and data.get('results', 0) > 0:
            team_info = data['response'][0]['team']
            log.info(f"Найдена команда '{team_info['name']}' с ID {team_info['id']}")
            
            # Возвращаем не словарь, а объект Team, как вы и сделали
            return Team(
                id=team_info['id'],
                name=team_info['name'],
                logo_url=team_info['logo']
            )
            
        log.warning(f"Команда '{team_name}' не найдена через API-Football.")
        return None

    def fetch_team_statistics(self, team_id: int, league_id: int, season: int) -> Optional[Dict[str, Any]]:
        """
        Получает статистику команды для лиги и сезона.
        Этот метод предназначен для вызова из фонового потока (QThread).

        Args:
            team_id (int): ID команды.
            league_id (int): ID лиги.
            season (int): Год сезона.

        Returns:
            Optional[dict]: Словарь со статистикой или None, если ничего не найдено.
            
        Raises:
            ApiClientError: В случае сетевых проблем или ошибок API.
        """
        log.info(f"Запрашиваю статистику для команды ID {team_id}, лига ID {league_id}...")
        
        params = {'league': league_id, 'season': season, 'team': team_id}
        data = self._make_request("teams/statistics", params=params)
        
        if data and data.get('results', 0) > 0:
            log.info(f"Статистика для команды ID {team_id} успешно получена.")
            return data['response']
            
        log.warning(f"Статистика для команды ID {team_id} не найдена.")
        return None