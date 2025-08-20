import datetime
import sqlite3
import json
from contextlib import contextmanager
import time
from config import DATABASE_CONFIG, RAW_TABLE, TRANSFORMED_TABLE
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
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
                    -- Match data
                    report_link TEXT UNIQUE,
                    date TEXT,
                    home TEXT,
                    score TEXT,
                    away TEXT,
                    attendance TEXT,
                    team_stats TEXT,
                    extra_stats TEXT,
                    
                    -- Metadata
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    PRIMARY KEY (report_link)
                )
            """
            )

            # Create indexes
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_report_link ON {RAW_TABLE}(report_link)"
            )
            conn.commit()

    def initialize_transformed_table(self):
        """Create transformed table with all structured columns"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TRANSFORMED_TABLE} (
                    -- Original match data
                    report_link TEXT NOT NULL UNIQUE,
                    
                    -- Transformed team stats
                    home_possession REAL,
                    away_possession REAL,
                    home_passing_attemps INTEGER,
                    home_passes_completed INTEGER,
                    away_passing_attemps INTEGER,
                    away_passes_completed INTEGER,
                    home_shots_attemps INTEGER,
                    home_shots_on_target INTEGER,
                    away_shots_attemps INTEGER,
                    away_shots_on_target INTEGER,
                    home_saves_attemps INTEGER,
                    home_saves_completed INTEGER,
                    away_saves_attempts INTEGER,
                    away_saves_completed INTEGER,
                    
                    -- Transformed extra stats
                    home_fouls INTEGER,
                    away_fouls INTEGER,
                    home_corners INTEGER,
                    away_corners INTEGER,
                    home_crosses INTEGER,
                    away_crosses INTEGER,
                    home_touches INTEGER,
                    away_touches INTEGER,
                    home_tackles INTEGER,
                    away_tackles INTEGER,
                    home_interceptions INTEGER,
                    away_interceptions INTEGER,
                    home_aerials_won INTEGER,
                    away_aerials_won INTEGER,
                    home_clearances INTEGER,
                    away_clearances INTEGER,
                    home_offsides INTEGER,
                    away_offsides INTEGER,
                    home_goal_kicks INTEGER,
                    away_goal_kicks INTEGER,
                    home_throw_ins INTEGER,
                    away_throw_ins INTEGER,
                    home_long_balls INTEGER,
                    away_long_balls INTEGER,
                    
                    -- Metadata
                    date_added TIMESTAMP,
                    last_updated TIMESTAMP,
                    
                    PRIMARY KEY (report_link)
                )
                """
            )

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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    def execute_query(self, query: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()


if __name__ == "__main__":
    db = DatabaseManager()
    db._delete_tables([RAW_TABLE, TRANSFORMED_TABLE])
