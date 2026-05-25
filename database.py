"""
Модуль для работы с базой данных SQLite3.

Предоставляет класс для выполнения CRUD-операций с использованием контекстных менеджеров.
"""

import logging
import sqlite3
from typing import Any, Optional, Sequence

logger = logging.getLogger(__name__)


class Database:
    """
    Класс для работы с SQLite3 базой данных.

    Поддерживает подключение, отключение и выполнение различных операций
    с использованием контекстных менеджеров для автоматического управления ресурсами.
    """

    def __init__(self, db_path: str):
        """
        Инициализирует экземпляр класса Database.

        :param db_path: Путь к файлу базы данных SQLite.
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """
        Устанавливает подключение к базе данных.

        Создает новое соединение с SQLite базой данных.
        Если подключение уже установлено, ничего не делает.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"Подключение к базе данных установлено: {self.db_path}")
        else:
            logger.debug("Подключение к базе данных уже установлено")

    def disconnect(self) -> None:
        """
        Закрывает подключение к базе данных.

        Если подключение активно, закрывает его и сбрасывает ссылку.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Подключение к базе данных закрыто")
        else:
            logger.debug("Подключение к базе данных уже закрыто")

    def __enter__(self) -> "Database":
        """
        Метод контекстного менеджера для входа.

        :return: Экземпляр Database с активным подключением.
        """
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Метод контекстного менеджера для выхода.

        Закрывает подключение при выходе из контекста.

        :param exc_type: Тип исключения (если было).
        :param exc_val: Значение исключения (если было).
        :param exc_tb: Трассировка исключения (если было).
        """
        self.disconnect()

    def _get_cursor(self) -> sqlite3.Cursor:
        """
        Возвращает курсор для выполнения SQL-запросов.

        :return: Объект курсора.
        :raises RuntimeError: Если подключение не установлено.
        """
        if self._connection is None:
            logger.error("Попытка выполнить запрос без подключения к БД")
            raise RuntimeError("Подключение к базе данных не установлено. Вызовите connect() или используйте контекстный менеджер.")
        return self._connection.cursor()

    def execute(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
        commit: bool = True
    ) -> sqlite3.Cursor:
        """
        Выполняет SQL-запрос.

        Универсальный метод для выполнения произвольных SQL-запросов.

        :param query: SQL-запрос в виде строки.
        :param params: Параметры запроса (кортеж или список).
        :param commit: Флаг подтверждения изменений. По умолчанию True.
        :return: Объект курсора с результатами выполнения.
        """
        logger.debug(f"Выполнение запроса: {query[:100]}...")
        cursor = self._get_cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if commit:
            self._connection.commit()
            logger.debug("Транзакция подтверждена")

        return cursor

    def executemany(
        self,
        query: str,
        params_list: Sequence[Sequence[Any]],
        commit: bool = True
    ) -> sqlite3.Cursor:
        """
        Выполняет SQL-запрос для множества параметров.

        Полезно для пакетной вставки или обновления данных.

        :param query: SQL-запрос в виде строки.
        :param params_list: Список кортежей с параметрами.
        :param commit: Флаг подтверждения изменений. По умолчанию True.
        :return: Объект курсора.
        """
        logger.debug(f"Пакетный запрос, {len(params_list)} записей: {query[:100]}...")
        cursor = self._get_cursor()
        cursor.executemany(query, params_list)

        if commit:
            self._connection.commit()
            logger.debug("Пакетная транзакция подтверждена")

        return cursor

    def fetch_one(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None
    ) -> Optional[dict]:
        """
        Выполняет запрос и возвращает одну запись.

        :param query: SQL-запрос для SELECT.
        :param params: Параметры запроса.
        :return: Словарь с данными первой найденной записи или None.
        """
        cursor = self.execute(query, params, commit=False)
        row = cursor.fetchone()
        logger.debug(f"Получена запись: {row is not None}")
        return dict(row) if row else None

    def fetch_all(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None
    ) -> list[dict]:
        """
        Выполняет запрос и возвращает все записи.

        :param query: SQL-запрос для SELECT.
        :param params: Параметры запроса.
        :return: Список словарей с данными найденных записей.
        """
        cursor = self.execute(query, params, commit=False)
        rows = cursor.fetchall()
        logger.debug(f"Получено записей: {len(rows)}")
        return [dict(row) for row in rows]

    def fetch_many(
        self,
        query: str,
        size: int,
        params: Optional[Sequence[Any]] = None
    ) -> list[dict]:
        """
        Выполняет запрос и возвращает указанное количество записей.

        :param query: SQL-запрос для SELECT.
        :param size: Количество записей для возврата.
        :param params: Параметры запроса.
        :return: Список словарей с данными записей.
        """
        cursor = self.execute(query, params, commit=False)
        rows = cursor.fetchmany(size)
        logger.debug(f"Получено записей: {len(rows)} из {size}")
        return [dict(row) for row in rows]

    def insert(self, table: str, data: dict) -> int:
        """
        Вставляет новую запись в таблицу.

        :param table: Имя таблицы.
        :param data: Словарь с данными для вставки (ключ=имя колонки, значение=значение).
        :return: ID вставленной записи.
        """
        logger.info(f"Вставка записи в таблицу '{table}': {data}")
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.execute(query, tuple(data.values()))
        logger.info(f"Запись вставлена, ID: {cursor.lastrowid}")
        return cursor.lastrowid

    def insert_many(self, table: str, data_list: list[dict]) -> list[int]:
        """
        Вставляет множество записей в таблицу.

        :param table: Имя таблицы.
        :param data_list: Список словарей с данными для вставки.
        :return: Список ID вставленных записей.
        """
        if not data_list:
            logger.warning("Попытка вставки пустого списка записей")
            return []

        logger.info(f"Пакетная вставка {len(data_list)} записей в таблицу '{table}'")
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?"] * len(data_list[0]))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        params_list = [tuple(record.values()) for record in data_list]
        self.executemany(query, params_list)

        # Получаем ID всех вставленных записей
        ids = []
        for _ in data_list:
            ids.append(self._get_cursor().lastrowid)

        logger.info(f"Вставлено {len(ids)} записей")
        return ids

    def select(
        self,
        table: str,
        columns: Optional[list[str]] = None,
        where: Optional[str] = None,
        params: Optional[Sequence[Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[dict]:
        """
        Выбирает записи из таблицы.

        :param table: Имя таблицы.
        :param columns: Список колонок для выборки. Если None, выбирает все (*).
        :param where: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :param order_by: Сортировка (без ключевого слова ORDER BY).
        :param limit: Ограничение количества записей.
        :param offset: Смещение для пагинации.
        :return: Список словарей с данными записей.
        """
        cols = ", ".join(columns) if columns else "*"
        query = f"SELECT {cols} FROM {table}"

        if where:
            query += f" WHERE {where}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit is not None:
            query += f" LIMIT {limit}"

        if offset is not None:
            query += f" OFFSET {offset}"

        logger.debug(f"Выборка из таблицы '{table}'{f' по условию: {where}' if where else ''}")
        return self.fetch_all(query, params)

    def select_one(
        self,
        table: str,
        columns: Optional[list[str]] = None,
        where: Optional[str] = None,
        params: Optional[Sequence[Any]] = None
    ) -> Optional[dict]:
        """
        Выбирает одну запись из таблицы.

        :param table: Имя таблицы.
        :param columns: Список колонок для выборки. Если None, выбирает все (*).
        :param where: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :return: Словарь с данными записи или None.
        """
        logger.debug(f"Выборка одной записи из таблицы '{table}'")
        cols = ", ".join(columns) if columns else "*"
        query = f"SELECT {cols} FROM {table}"

        if where:
            query += f" WHERE {where}"

        return self.fetch_one(query, params)

    def update(
        self,
        table: str,
        data: dict,
        where: str,
        params: Optional[Sequence[Any]] = None
    ) -> int:
        """
        Обновляет записи в таблице.

        :param table: Имя таблицы.
        :param data: Словарь с данными для обновления (ключ=имя колонки, значение=новое значение).
        :param where: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :return: Количество обновлённых записей.
        """
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params_values = tuple(data.values())
        if params:
            params_values = params_values + tuple(params)

        cursor = self.execute(query, params_values)
        logger.info(f"Обновлено записей: {cursor.rowcount}")
        return cursor.rowcount

    def delete(self, table: str, where: str, params: Optional[Sequence[Any]] = None) -> int:
        """
        Удаляет записи из таблицы.

        :param table: Имя таблицы.
        :param where: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :return: Количество удалённых записей.
        """
        logger.info(f"Удаление записей из таблицы '{table}' по условию: {where}")
        query = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(query, params)
        logger.info(f"Удалено записей: {cursor.rowcount}")
        return cursor.rowcount

    def execute_script(self, script: str) -> None:
        """
        Выполняет SQL-скрипт с множеством команд.

        Полезно для выполнения DDL-операций (CREATE TABLE, DROP TABLE и т.д.).

        :param script: SQL-скрипт в виде строки.
        """
        logger.info(f"Выполнение SQL-скрипта: {script[:50]}...")
        self._get_cursor().executescript(script)
        self._connection.commit()
        logger.info("SQL-скрипт выполнен успешно")

    def table_exists(self, table_name: str) -> bool:
        """
        Проверяет существование таблицы в базе данных.

        :param table_name: Имя таблицы для проверки.
        :return: True если таблица существует, False иначе.
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.fetch_one(query, (table_name,))
        exists = result is not None
        logger.debug(f"Таблица '{table_name}' существует: {exists}")
        return exists

    def get_table_schema(self, table_name: str) -> list[dict]:
        """
        Получает схему таблицы (колонки и их типы).

        :param table_name: Имя таблицы.
        :return: Список словарей с информацией о колонках.
        """
        logger.debug(f"Получение схемы таблицы '{table_name}'")
        query = f"PRAGMA table_info({table_name})"
        cursor = self.execute(query, commit=False)
        columns = cursor.fetchall()
        logger.debug(f"Найдено колонок: {len(columns)}")
        return [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default_value": row[4],
                "pk": row[5]
            }
            for row in columns
        ]

    def get_all_tables(self) -> list[str]:
        """
        Получает список всех таблиц в базе данных.

        :return: Список имён таблиц.
        """
        logger.debug("Получение списка всех таблиц")
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        rows = self.fetch_all(query)
        tables = [row["name"] for row in rows]
        logger.debug(f"Найдено таблиц: {len(tables)}")
        return tables

    def get_last_insert_id(self) -> int:
        """
        Получает ID последней вставленной записи.

        :return: ID последней вставленной записи.
        """
        cursor = self._get_cursor()
        return cursor.lastrowid

    def get_row_count(self, table: str, where: Optional[str] = None, params: Optional[Sequence[Any]] = None) -> int:
        """
        Получает количество записей в таблице.

        :param table: Имя таблицы.
        :param where: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :return: Количество записей.
        """
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where:
            query += f" WHERE {where}"

        result = self.fetch_one(query, params)
        count = result["count"] if result else 0
        logger.debug(f"Количество записей в '{table}': {count}")
        return count

    def begin_transaction(self) -> None:
        """
        Начинает транзакцию.

        Все последующие операции будут выполнены в рамках одной транзакции
        до вызова commit() или rollback().
        """
        logger.info("Начало транзакции")
        if self._connection:
            self._connection.execute("BEGIN")

    def commit(self) -> None:
        """
        Коммитит текущую транзакцию.

        Сохраняет все изменения, сделанные с момента начала транзакции.
        """
        logger.info("Подтверждение транзакции")
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        """
        Откатывает текущую транзакцию.

        Отменяет все изменения, сделанные с момента начала транзакции.
        """
        logger.warning("Откат транзакции")
        if self._connection:
            self._connection.rollback()


class DatabaseManager:
    """
    Обёртка над классом Database для более удобного API.

    Предоставляет методы с иными именами для совместимости с существующим кодом.
    """

    def __init__(self, db_path: str):
        """
        Инициализирует менеджер базы данных.

        :param db_path: Путь к файлу базы данных SQLite.
        """
        self._db = Database(db_path)

    def __enter__(self) -> "DatabaseManager":
        """Вход в контекстный менеджер."""
        self._db.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Выход из контекстного менеджера."""
        self._db.__exit__(exc_type, exc_val, exc_tb)

    def select_records(
        self,
        table_name: str,
        columns: Optional[list[str]] = None,
        where_clause: Optional[str] = None,
        params: Optional[Sequence[Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[dict]:
        """
        Выбирает записи из таблицы.

        :param table_name: Имя таблицы.
        :param columns: Список колонок для выборки. Если None, выбирает все (*).
        :param where_clause: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :param order_by: Сортировка (без ключевого слова ORDER BY).
        :param limit: Ограничение количества записей.
        :param offset: Смещение для пагинации.
        :return: Список словарей с данными записей.
        """
        return self._db.select(
            table=table_name,
            columns=columns,
            where=where_clause,
            params=params,
            order_by=order_by,
            limit=limit,
            offset=offset
        )

    def insert_record(self, table_name: str, data: dict) -> int:
        """
        Вставляет новую запись в таблицу.

        :param table_name: Имя таблицы.
        :param data: Словарь с данными для вставки.
        :return: ID вставленной записи.
        """
        return self._db.insert(table=table_name, data=data)

    def update_records(
        self,
        table_name: str,
        data: dict,
        where_clause: str,
        params: Optional[Sequence[Any]] = None
    ) -> int:
        """
        Обновляет записи в таблице.

        :param table_name: Имя таблицы.
        :param data: Словарь с данными для обновления.
        :param where_clause: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :return: Количество обновлённых записей.
        """
        return self._db.update(table=table_name, data=data, where=where_clause, params=params)

    def delete_records(self, table_name: str, where_clause: str, params: Optional[Sequence[Any]] = None) -> int:
        """
        Удаляет записи из таблицы.

        :param table_name: Имя таблицы.
        :param where_clause: Условие WHERE (без ключевого слова WHERE).
        :param params: Параметры для условия WHERE.
        :return: Количество удалённых записей.
        """
        return self._db.delete(table=table_name, where=where_clause, params=params)

    def execute_query(self, query: str, params: Optional[Sequence[Any]] = None) -> sqlite3.Cursor:
        """
        Выполняет произвольный SQL-запрос.

        :param query: SQL-запрос.
        :param params: Параметры запроса.
        :return: Курсор с результатами.
        """
        return self._db.execute(query, params)
