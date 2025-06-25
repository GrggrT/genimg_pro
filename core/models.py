# core/models.py

from sqlalchemy import (create_engine, Column, Integer, String, Text, 
                        ForeignKey)
from sqlalchemy.orm import declarative_base, relationship
from config import DATABASE_PATH

Base = declarative_base()

class Team(Base):
    """
    Основная модель для команды.
    Хранит уникальную информацию о команде.
    """
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    name_normalized = Column(String, unique=True, nullable=False, index=True)
    logo_filename = Column(Text)
    api_source = Column(String)
    last_updated_ts = Column(Integer)

    # Связь "один ко многим": одна команда может иметь много псевдонимов
    aliases = relationship("TeamAlias", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

class TeamAlias(Base):
    """
    Модель для псевдонимов команд.
    Каждая запись ссылается на основную команду.
    """
    __tablename__ = 'team_aliases'

    id = Column(Integer, primary_key=True)
    alias = Column(String, unique=True, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)

    # Связь "многие к одному": много псевдонимов могут ссылаться на одну команду
    team = relationship("Team", back_populates="aliases")

    def __repr__(self):
        return f"<TeamAlias(id={self.id}, alias='{self.alias}')>"

def get_engine():
    """Возвращает экземпляр движка SQLAlchemy."""
    return create_engine(f'sqlite:///{DATABASE_PATH}')