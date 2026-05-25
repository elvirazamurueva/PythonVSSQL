"""
Скрипт для импорта данных из CSV файла imdb_top_250.csv в базу данных base.db.
"""

import csv
from database import Database


def create_movies_table(db: Database) -> None:
    """Создаёт таблицу movies в базе данных."""
    db.execute_script("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            title TEXT NOT NULL,
            year INTEGER,
            genre TEXT,
            duration TEXT,
            origin TEXT,
            director TEXT,
            imdb_rating REAL,
            rating_count INTEGER,
            imdb_link TEXT
        )
    """)
    print("Таблица 'movies' готова.")


def parse_duration(duration: str) -> int | None:
    """Преобразует строку длительности (например, '2h 42min') в минуты."""
    if not duration:
        return None
    
    total_minutes = 0
    duration = duration.strip()
    
    # Ищем часы
    if 'h' in duration:
        parts = duration.split('h')
        hours_part = parts[0].strip()
        if hours_part.isdigit():
            total_minutes += int(hours_part) * 60
        if len(parts) > 1:
            duration = parts[1].strip()
    
    # Ищем минуты
    if 'min' in duration:
        minutes_part = duration.replace('min', '').strip()
        if minutes_part.isdigit():
            total_minutes += int(minutes_part)
    
    return total_minutes if total_minutes > 0 else None


def import_csv_to_db(csv_path: str, db_path: str) -> None:
    """
    Импортирует данные из CSV файла в базу данных SQLite.
    
    :param csv_path: Путь к CSV файлу.
    :param db_path: Путь к файлу базы данных SQLite.
    """
    print(f"Начало импорта из {csv_path} в {db_path}...")
    
    with Database(db_path) as db:
        # Создаём таблицу
        create_movies_table(db)
        
        # Проверяем, есть ли уже данные
        existing_count = db.get_row_count("movies")
        if existing_count > 0:
            response = input(f"В таблице уже есть {existing_count} записей. Очистить таблицу? (y/n): ")
            if response.lower() == 'y':
                db.execute("DELETE FROM movies")
                print("Таблица очищена.")
            else:
                print("Импорт отменён.")
                return
        
        # Читаем CSV файл
        movies_data = []
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                movie = {
                    "rank": int(row[""]) if row[""] else None,  # Первый столбец - это индекс
                    "title": row["Title"],
                    "year": int(row["Year"]) if row["Year"] else None,
                    "genre": row["Genre"],
                    "duration": row["Duration"],
                    "origin": row["Origin"],
                    "director": row["Director"],
                    "imdb_rating": float(row["IMDB rating"]) if row["IMDB rating"] else None,
                    "rating_count": int(row["Rating count"]) if row["Rating count"] else None,
                    "imdb_link": row["IMDB link"]
                }
                movies_data.append(movie)
        
        print(f"Прочитано {len(movies_data)} фильмов из CSV файла.")
        
        # Пакетная вставка данных
        db.begin_transaction()
        try:
            db.insert_many("movies", movies_data)
            db.commit()
            print(f"Успешно импортировано {len(movies_data)} фильмов в базу данных.")
        except Exception as e:
            db.rollback()
            print(f"Ошибка при импорте: {e}")
            raise


if __name__ == "__main__":
    CSV_FILE = "imdb_top_250.csv"
    DB_FILE = "base.db"
    
    import_csv_to_db(CSV_FILE, DB_FILE)
