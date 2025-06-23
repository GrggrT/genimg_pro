# core/cache_manager.py

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List

class CacheManager:
    """
    Управляет кэшем данных команд в базе данных SQLite.

    Отвечает за создание таблиц, добавление новых команд и их поиск
    по имени или псевдонимам.
    """
    def __init__(self, db_path: str) -> None:
        """
        Инициализирует менеджер кэша.

        Args:
            db_path (str): Путь к файлу базы данных SQLite.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Создает необходимые таблицы в БД, если они не существуют."""
        with self._connection:
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    logo_path TEXT NOT NULL,
                    api_source TEXT
                )
            """)
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS team_aliases (
                    id INTEGER PRIMARY KEY,
                    team_id INTEGER,
                    alias TEXT NOT NULL UNIQUE,
                    FOREIGN KEY(team_id) REFERENCES teams(id)
                )
            """)

    def add_team_to_cache(self, name: str, logo_path: str, api_source: str, aliases: Optional[List[str]] = None) -> None:
        """
        Добавляет новую команду и ее псевдонимы в кэш.

        Args:
            name (str): Официальное название команды.
            logo_path (str): Путь к файлу с логотипом.
            api_source (str): Источник данных (например, 'api-football').
            aliases (Optional[List[str]]): Список псевдонимов для команды.
        """
        with self._connection:
            cursor = self._connection.cursor()
            cursor.execute("INSERT INTO teams (name, logo_path, api_source) VALUES (?, ?, ?)",
                           (name, logo_path, api_source))
            team_id = cursor.lastrowid
            if aliases:
                for alias in aliases:
                    cursor.execute("INSERT INTO team_aliases (team_id, alias) VALUES (?, ?)",
                                   (team_id, alias.lower()))
            # Добавляем само имя команды как псевдоним в нижнем регистре
            cursor.execute("INSERT INTO team_aliases (team_id, alias) VALUES (?, ?)",
                           (team_id, name.lower()))


    def find_team_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Ищет команду в кэше по имени или псевдониму.

        Args:
            name (str): Имя или псевдоним команды для поиска.

        Returns:
            Optional[Dict[str, Any]]: Словарь с данными команды, если найдена, иначе None.
        """
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT t.id, t.name, t.logo_path, t.api_source
            FROM teams t
            JOIN team_aliases ta ON t.id = ta.team_id
            WHERE ta.alias = ?
        """, (name.lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None