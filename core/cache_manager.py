# core/cache_manager.py

import os
import time
from sqlalchemy.orm import sessionmaker, joinedload
from core.models import Team, TeamAlias, get_engine # Предполагаем, что у вас есть модели Team и TeamAlias
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
        Включает проверку на срок годности кэша и наличие файла логотипа.
        """
        normalized_alias = self._normalize_name(alias)
        session = self.Session()
        try:
            # Ищем псевдоним и сразу подгружаем связанную команду
            team_alias = (
                session.query(TeamAlias)
                .options(joinedload(TeamAlias.team))
                .filter(TeamAlias.alias == normalized_alias)
                .first()
            )

            if not team_alias or not team_alias.team:
                print(f"КЭШ: Псевдоним '{normalized_alias}' не найден.")
                return None

            team = team_alias.team
            
            # Проверяем, не устарел ли кэш
            cache_lifetime_seconds = CACHE_EXPIRATION_DAYS * 24 * 60 * 60
            if time.time() - team.last_updated_ts > cache_lifetime_seconds:
                print(f"КЭШ: Запись для '{team.name}' устарела. Требуется обновление.")
                return None
            
            # Проверяем, существует ли файл логотипа
            logo_full_path = os.path.join(LOGO_DIR, team.logo_filename)
            if not os.path.exists(logo_full_path):
                 print(f"КЭШ: Файл логотипа для '{team.name}' не найден по пути {logo_full_path}. Требуется обновление.")
                 return None

            print(f"КЭШ: Команда '{team.name}' найдена в кэше по псевдониму '{normalized_alias}'.")
            return team
        finally:
            session.close()

    def add_or_update_team(self, team_name: str, logo_filename: str, api_source: str, aliases: list[str]):
        """
        Интеллектуально добавляет или обновляет команду и её псевдонимы.
        - Находит или создает основную запись о команде.
        - Добавляет только новые, уникальные псевдонимы.
        """
        normalized_team_name = self._normalize_name(team_name)
        session = self.Session()
        try:
            # 1. Найти или создать основную запись о команде
            team = session.query(Team).filter(Team.name_normalized == normalized_team_name).first()
            
            if team:
                # Команда уже существует, обновляем данные
                print(f"КЭШ: Обновление существующей команды '{team_name}'.")
                team.logo_filename = logo_filename
                team.api_source = api_source
                team.last_updated_ts = int(time.time())
            else:
                # Команды нет, создаем новую
                print(f"КЭШ: Создание новой команды '{team_name}'.")
                team = Team(
                    name=team_name,
                    name_normalized=normalized_team_name,
                    logo_filename=logo_filename,
                    api_source=api_source,
                    last_updated_ts=int(time.time())
                )
                session.add(team)
            
            # Предварительная фиксация, чтобы получить team.id для новой команды
            session.flush()

            # 2. Добавить только новые псевдонимы
            for alias_str in aliases:
                normalized_alias = self._normalize_name(alias_str)
                # Проверяем, существует ли уже такой псевдоним
                alias_exists = session.query(TeamAlias).filter(TeamAlias.alias == normalized_alias).first()
                if not alias_exists:
                    print(f"КЭШ: Добавление нового псевдонима '{normalized_alias}' для команды '{team.name}'.")
                    new_alias = TeamAlias(alias=normalized_alias, team_id=team.id)
                    session.add(new_alias)
                else:
                    print(f"КЭШ: Псевдоним '{normalized_alias}' уже существует.")

            session.commit()
        except Exception as e:
            print(f"КЭШ: Ошибка при добавлении/обновлении записи: {e}")
            session.rollback()
        finally:
            session.close()