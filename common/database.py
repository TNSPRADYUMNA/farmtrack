"""PostgreSQL in deployment; optional SQLite for a local teaching demo."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, schema):
        self.schema = schema
        self.local = os.getenv('DATABASE_MODE') == 'sqlite'

    @contextmanager
    def connect(self):
        if self.local:
            directory = Path(os.getenv('SQLITE_DIRECTORY', '.local-data'))
            directory.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(directory / f'{self.schema}.db', timeout=15)
            connection.row_factory = sqlite3.Row
        else:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                dbname=os.getenv('DB_NAME', 'farmtrack'),
                user=os.getenv('DB_USER', 'farmtrack'),
                password=os.environ['DB_PASSWORD'],
                connect_timeout=5, row_factory=dict_row,
                options=f'-c search_path={self.schema},public')
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self, ddl):
        with self.connect() as connection:
            if not self.local:
                # Serializes concurrent replica initialization, including CREATE SCHEMA.
                connection.execute('SELECT pg_advisory_xact_lock(73021)')
                connection.execute(f'CREATE SCHEMA IF NOT EXISTS {self.schema}')
            connection.execute(ddl)

    def query(self, sql, params=(), one=False):
        with self.connect() as connection:
            cursor = connection.execute(sql if self.local else sql.replace('?', '%s'), params)
            if cursor.description is None:
                return None
            rows = [dict(row) for row in cursor.fetchall()]
            return (rows[0] if rows else None) if one else rows
