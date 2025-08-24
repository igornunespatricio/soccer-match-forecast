import datetime
import sqlite3
import json
from contextlib import contextmanager
import time
from config import (
    DATABASE_CONFIG,
    RAW_TABLE,
    TRANSFORMED_TABLE,
    RAW_TABLE_QUERY,
    TRANSFOMED_TABLE_QUERY,
)
from logger import get_logger

logger = get_logger("Database")


class DatabaseManager:
    def __init__(self):
        self.config = DATABASE_CONFIG

    @contextmanager
    def get_connection(self):
        if self.config["engine"] == "sqlite":
            conn = sqlite3.connect(self.config["sqlite_path"])
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        else:
            import psycopg2

            conn = psycopg2.connect(**self.config["postgresql"])

        try:
            yield conn
        finally:
            conn.close()

    def initialize_raw_table(self):
        """Create raw table with all columns"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(RAW_TABLE_QUERY)

            # Create indexes
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_report_link ON {RAW_TABLE}(report_link)"
            )
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_match_composite ON {RAW_TABLE}(date, home, away)"
            )
            conn.commit()

    def initialize_transformed_table(self):
        """Create transformed table with all structured columns"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(TRANSFOMED_TABLE_QUERY)

            # Create indexes
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_report_link ON {TRANSFORMED_TABLE}(report_link)"
            )
            conn.commit()

    def initialize_db(self):
        """initialize_db creates the necessary tables and indexes for the database."""
        self.initialize_raw_table()
        self.initialize_transformed_table()

    def _delete_tables(self, table_names: list[str]):
        """Delete listed tables. BE CAREFULLY!"""
        for table_name in table_names:
            self._delete_table(table_name)

    def _delete_table(self, table_name):
        self.execute_query(f"DROP TABLE IF EXISTS {table_name}")

    def _delete_all_data(self, table_name):
        self.execute_query(f"DELETE FROM {table_name}")

    def execute_query(self, query: str, params: tuple = None) -> list[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            conn.commit()

        return results


if __name__ == "__main__":
    db = DatabaseManager()
    db.initialize_db()
    # db._delete_all_data(TRANSFORMED_TABLE)
    # db._delete_table(TRANSFORMED_TABLE)
