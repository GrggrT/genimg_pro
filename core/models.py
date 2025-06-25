# core/models.py

from sqlalchemy import (create_engine, Column, Integer, String, Text,
                        ForeignKey)
from sqlalchemy.orm import declarative_base, relationship
from config import DATABASE_PATH

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams' # Имя этой таблицы правильное

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    name_normalized = Column(String, unique=True, nullable=False, index=True)
    logo_filename = Column(Text)
    api_source = Column(String)
    last_updated_ts = Column(Integer)
    aliases = relationship("TeamAlias", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

class TeamAlias(Base):
    # !!! ВОТ ВАЖНОЕ ИЗМЕНЕНИЕ !!!
    __tablename__ = 'team_aliases' # Устанавливаем правильное имя таблицы

    id = Column(Integer, primary_key=True)
    alias = Column(String, unique=True, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    team = relationship("Team", back_populates="aliases")

    def __repr__(self):
        return f"<TeamAlias(id={self.id}, alias='{self.alias}')>"

def get_engine():
    """Возвращает экземпляр движка SQLAlchemy."""
    return create_engine(f'sqlite:///{DATABASE_PATH}')