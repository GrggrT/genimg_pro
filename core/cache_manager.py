# core/cache_manager.py

import os
import time
from sqlalchemy.orm import sessionmaker, joinedload
from core.models import Team, TeamAlias, get_engine
from config import CACHE_EXPIRATION_DAYS, LOGO_DIR

class CacheManager:
    """
    Управляет кэшем данных в базе данных SQLite через SQLAlchemy.
    """
    def __init__(self):
        engine = get_engine()
        self.Session = sessionmaker(bind=engine)

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    def find_team_by_alias(self, alias: str):
        """
        Ищет команду в кэше по её псевдониму.
        """
        normalized_alias = self._normalize_name(alias)
        session = self.Session()
        try:
            team_alias_obj = (
                session.query(TeamAlias)
                .options(joinedload(TeamAlias.team))
                .filter(TeamAlias.alias == normalized_alias)
                .first()
            )

            if not team_alias_obj or not team_alias_obj.team:
                print(f"КЭШ: Псевдоним '{normalized_alias}' не найден.")
                return None

            team = team_alias_obj.team
            
            cache_lifetime_seconds = CACHE_EXPIRATION_DAYS * 24 * 60 * 60
            if time.time() - team.last_updated_ts > cache_lifetime_seconds:
                print(f"КЭШ: Запись для '{team.name}' устарела.")
                return None
            
            logo_full_path = os.path.join(LOGO_DIR, team.logo_filename)
            if not os.path.exists(logo_full_path):
                 print(f"КЭШ: Файл логотипа для '{team.name}' не найден. Требуется обновление.")
                 return None

            print(f"КЭШ: Команда '{team.name}' найдена по псевдониму '{normalized_alias}'.")
            return team
        finally:
            session.close()

    def add_or_update_team(self, team_name: str, logo_filename: str, api_source: str, aliases: list[str]):
        """
        Интеллектуально добавляет или обновляет команду и её псевдонимы.
        """
        normalized_team_name = self._normalize_name(team_name)
        session = self.Session()
        try:
            team = session.query(Team).filter(Team.name_normalized == normalized_team_name).first()
            
            if team:
                print(f"КЭШ: Обновление команды '{team_name}'.")
                team.logo_filename = logo_filename
                team.api_source = api_source
                team.last_updated_ts = int(time.time())
            else:
                print(f"КЭШ: Создание новой команды '{team_name}'.")
                team = Team(
                    name=team_name,
                    name_normalized=normalized_team_name,
                    logo_filename=logo_filename,
                    api_source=api_source,
                    last_updated_ts=int(time.time())
                )
                session.add(team)
            
            session.flush()

            for alias_str in aliases:
                normalized_alias = self._normalize_name(alias_str)
                alias_exists = session.query(TeamAlias).filter(TeamAlias.alias == normalized_alias).first()
                if not alias_exists:
                    print(f"КЭШ: Добавление псевдонима '{normalized_alias}' для '{team.name}'.")
                    new_alias = TeamAlias(alias=normalized_alias, team_id=team.id)
                    session.add(new_alias)
            
            session.commit()
        except Exception as e:
            print(f"КЭШ: Ошибка при добавлении/обновлении: {e}")
            session.rollback()
        finally:
            session.close()