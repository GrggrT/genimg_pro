# core/cache_manager.py

import sqlite3
from typing import Optional, Dict, Any
from config import DATABASE_PATH # Импортируем путь к БД из центрального конфига

def get_db_connection():
    """
    Устанавливает и возвращает соединение с базой данных SQLite.
    Включает поддержку возврата данных в виде словарей.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    # Эта строка позволяет получать результаты запросов в виде словарей,
    # где ключи - это названия колонок. Это очень удобно.
    conn.row_factory = sqlite3.Row
    return conn

def find_team_by_alias(alias: str) -> Optional[Dict[str, Any]]:
    """
    Ищет команду в базе данных по её псевдониму.

    Сначала функция ищет точное совпадение в таблице псевдонимов ('aliases').
    Если совпадение найдено, она возвращает информацию об основной команде
    (имя и имя файла логотипа) из таблицы 'teams'.

    Args:
        alias (str): Псевдоним команды для поиска (например, "спартак", "bayern").

    Returns:
        Optional[Dict[str, Any]]: Словарь с данными команды
        (например, {'name': 'Spartak Moscow', 'logo_filename': 'Spartak Moscow.png'}),
        если команда найдена. В противном случае возвращает None.
    """
    if not isinstance(alias, str) or not alias.strip():
        return None

    # Приводим псевдоним к нижнему регистру для консистентного поиска
    search_alias = alias.strip().lower()

    query = """
    SELECT
        t.name,
        t.logo_filename
    FROM
        aliases a
    JOIN
        teams t ON a.team_id = t.id
    WHERE
        a.alias_name = ?
    """

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, (search_alias,))
        result = cursor.fetchone() # fetchone(), так как псевдоним уникален
        if result:
            # Преобразуем sqlite3.Row в стандартный dict для унификации
            return dict(result)
        return None
    finally:
        # Убедимся, что соединение всегда закрывается
        conn.close()

# --- Пример использования (для демонстрации) ---
# Этот блок выполнится, только если запустить этот файл напрямую:
# python core/cache_manager.py
if __name__ == '__main__':
    print("Демонстрация работы cache_manager.")
    print(f"Используется база данных: {DATABASE_PATH}")

    # Перед запуском этого примера убедитесь, что вы запустили
    # python setup_database.py для создания и наполнения БД.

    test_aliases = ["брюгге", "рапид вена", "rapid vienna", "несуществующая команда"]

    for test_alias in test_aliases:
        team_info = find_team_by_alias(test_alias)
        if team_info:
            print(f"Поиск по '{test_alias}': Найдена команда -> {team_info['name']} ({team_info['logo_filename']})")
        else:
            print(f"Поиск по '{test_alias}': Команда не найдена в кэше.")