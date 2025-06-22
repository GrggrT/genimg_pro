# core/cache_manager.py
import os
import time
from sqlalchemy.orm import sessionmaker
from core.models import TeamCache, get_engine
from config import CACHE_EXPIRATION_DAYS, LOGO_DIR

class CacheManager:
    """
    Класс для управления кэшем данных в базе данных SQLite через SQLAlchemy.
    """
    def __init__(self):
        """
        Инициализирует менеджер кэша, создавая сессию для работы с БД.
        """
        engine = get_engine()
        self.Session = sessionmaker(bind=engine)

    def _normalize_name(self, name: str) -> str:
        """
        Приводит имя команды к стандартному виду для поиска и сохранения.
        """
        return name.strip().lower()

    def find_team_by_name(self, team_name: str):
        """
        Ищет команду в кэше по её нормализованному имени.

        Args:
            team_name (str): Имя команды для поиска.

        Returns:
            TeamCache | None: Объект команды, если она найдена и кэш не устарел,
                              иначе None.
        """
        normalized_name = self._normalize_name(team_name)
        session = self.Session()
        try:
            team = session.query(TeamCache).filter_by(team_name_normalized=normalized_name).first()

            if not team:
                print(f"КЭШ: Команда '{normalized_name}' не найдена.")
                return None

            # Проверяем, не устарел ли кэш
            cache_lifetime_seconds = CACHE_EXPIRATION_DAYS * 24 * 60 * 60
            if time.time() - team.last_updated_ts > cache_lifetime_seconds:
                print(f"КЭШ: Запись для '{normalized_name}' устарела. Требуется обновление.")
                return None
            
            # Проверяем, существует ли файл логотипа
            if not os.path.exists(team.logo_path):
                 print(f"КЭШ: Файл логотипа для '{normalized_name}' не найден по пути {team.logo_path}. Требуется обновление.")
                 return None

            print(f"КЭШ: Команда '{normalized_name}' найдена в кэше.")
            return team
        finally:
            session.close()

    def add_team_to_cache(self, team_name: str, logo_path: str, api_source: str):
        """
        Добавляет или обновляет запись о команде в кэше.

        Args:
            team_name (str): Имя команды.
            logo_path (str): Путь к файлу логотипа.
            api_source (str): Источник API ('api-football', 'thesportsdb').
        """
        normalized_name = self._normalize_name(team_name)
        session = self.Session()
        try:
            # Ищем существующую запись
            team = session.query(TeamCache).filter_by(team_name_normalized=normalized_name).first()
            
            if team:
                # Обновляем существующую
                team.logo_path = logo_path
                team.api_source = api_source
                team.last_updated_ts = int(time.time())
                print(f"КЭШ: Запись для '{normalized_name}' обновлена.")
            else:
                # Создаем новую
                new_team = TeamCache(
                    team_name_normalized=normalized_name,
                    logo_path=logo_path,
                    api_source=api_source,
                    last_updated_ts=int(time.time())
                )
                session.add(new_team)
                print(f"КЭШ: Новая запись для '{normalized_name}' добавлена.")
            
            session.commit()
        except Exception as e:
            print(f"КЭШ: Ошибка при добавлении/обновлении записи: {e}")
            session.rollback()
        finally:
            session.close()