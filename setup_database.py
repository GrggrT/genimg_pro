# setup_database.py
import os
from sqlalchemy import create_engine
from config import DATABASE_PATH
from core.models import Base  # Импортируем именно Base из моделей

def setup_database():
    """
    Инициализирует базу данных и создает ВСЕ таблицы,
    определенные в core.models.py.
    """
    # Проверяем, существует ли папка, в которой должна быть БД.
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir) and db_dir:
        os.makedirs(db_dir)
        print(f"Создана директория: {db_dir}")

    # Создаем движок, который будет работать с нашей базой данных
    engine = create_engine(f'sqlite:///{DATABASE_PATH}')

    print("Создание таблиц в базе данных на основе core.models.py...")
    # Эта команда - источник правды. Она смотрит в core.models.py
    # и создает все таблицы, которые там описаны (Team и TeamAlias)
    # с их правильными именами ('teams' и 'team_aliases').
    Base.metadata.create_all(engine)
    
    print(f"База данных успешно создана/обновлена по пути: {DATABASE_PATH}")
    print("Все таблицы, определенные в моделях, были созданы.")

if __name__ == "__main__":
    setup_database()