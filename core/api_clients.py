# core/api_clients.py

import requests
from typing import Optional, Dict, Any

class ApiFootballClient:
    """
    Клиент для взаимодействия с API-Football.

    Предоставляет методы для получения данных о футбольных командах.
    """
    def __init__(self, api_key: str) -> None:
        """
        Инициализирует API клиент.

        Args:
            api_key (str): Ваш API ключ для доступа к API-Football.
        """
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self.api_key
        }

    def fetch_team_data(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Ищет данные команды по ее названию через API.

        Args:
            team_name (str): Название команды для поиска.

        Returns:
            Optional[Dict[str, Any]]: Словарь с данными о команде
            (id, name, logo_url), если команда найдена, иначе None.
        """
        response = requests.get(
            f"{self.base_url}/teams",
            headers=self.headers,
            params={"search": team_name}
        )
        response.raise_for_status()
        data = response.json()

        if data['results'] > 0:
            team_info = data['response'][0]['team']
            return {
                "id": team_info['id'],
                "name": team_info['name'],
                "logo_url": team_info['logo']
            }
        return None