# setup_database.py
import sqlite3
import os

# --- Настройки, необходимые для этого скрипта ---
# Убедитесь, что этот скрипт находится в корневой папке проекта
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(PROJECT_ROOT, "cache.db")

# --- ВАШ БОЛЬШОЙ СЛОВАРЬ ---
# Я взял его из вашего файла team_mappings_fixed.py.
# Теперь он находится здесь, чтобы скрипт был самодостаточным.
LEAGUE_TEAMS_MAPPINGS = {
    "Austria - Bundesliga": {
        "рапид": "Rapid Vienna.png",
        "рапид вена": "Rapid Vienna.png",
        "rapid vienna": "Rapid Vienna.png",
        # ... и так далее, все ваши записи ...
    },
    "Belgium - Jupiler Pro League": {
        "брюгге": "Club Brugge KV.png",
        "клуб брюгге": "Club Brugge KV.png",
        # ... и так далее ...
    },
    # !! ВАЖНО: УБЕДИТЕСЬ, ЧТО ВЕСЬ ВАШ СЛОВАРЬ НАХОДИТСЯ ЗДЕСЬ !!
    # ... (вставьте сюда все остальные лиги из вашего файла)
}


def create_tables(conn):
    """Создает необходимые таблицы в базе данных, если их нет."""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        logo_filename TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aliases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER,
        alias_name TEXT NOT NULL UNIQUE,
        FOREIGN KEY (team_id) REFERENCES teams (id)
    );
    """)
    print("Таблицы 'teams' и 'aliases' созданы или уже существуют.")
    conn.commit()

def populate_database():
    """Наполняет базу данных командами и их псевдонимами."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # --- Наполняем таблицу команд ---
    unique_teams = {}
    for teams in LEAGUE_TEAMS_MAPPINGS.values():
        for logo_file in teams.values():
            if logo_file not in unique_teams:
                proper_name = os.path.splitext(logo_file)[0]
                unique_teams[logo_file] = proper_name

    inserted_teams = 0
    for logo_file, team_name in unique_teams.items():
        try:
            cursor.execute("INSERT INTO teams (name, logo_filename) VALUES (?, ?)", (team_name, logo_file))
            inserted_teams += 1
        except sqlite3.IntegrityError:
            pass
    
    print(f"Добавлено {inserted_teams} новых уникальных команд в базу данных.")

    # --- Наполняем таблицу псевдонимов ---
    inserted_aliases = 0
    flat_mappings = {}
    for teams in LEAGUE_TEAMS_MAPPINGS.values():
        for alias, logo_file in teams.items():
            flat_mappings[alias.lower()] = logo_file
    
    for alias, logo_file in flat_mappings.items():
        cursor.execute("SELECT id FROM teams WHERE logo_filename = ?", (logo_file,))
        result = cursor.fetchone()
        if result:
            team_id = result[0]
            try:
                cursor.execute("INSERT INTO aliases (team_id, alias_name) VALUES (?, ?)", (team_id, alias))
                inserted_aliases += 1
            except sqlite3.IntegrityError:
                pass
    
    print(f"Добавлено {inserted_aliases} новых псевдонимов в базу данных.")
    
    conn.commit()
    conn.close()
    print(f"База данных успешно наполнена.")

if __name__ == "__main__":
    db_conn = sqlite3.connect(DATABASE_PATH)
    create_tables(db_conn)
    db_conn.close()
    
    populate_database()