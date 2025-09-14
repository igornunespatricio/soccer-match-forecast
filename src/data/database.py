import pandas as pd
import datetime
import sqlite3
import json
from contextlib import contextmanager
import time

import pandas as pd
from src.config import (
    DATABASE_CONFIG,
    RAW_TABLE,
    TRANSFORMED_TABLE,
    RAW_TABLE_QUERY,
    TRANSFOMED_TABLE_QUERY,
)
from src.logger import get_logger

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
            # cursor.execute(RAW_TABLE_QUERY)
            cursor.executescript(RAW_TABLE_QUERY)

            # # Create indexes
            # cursor.execute(
            #     f"CREATE INDEX IF NOT EXISTS idx_report_link ON {RAW_TABLE}(report_link)"
            # )
            # cursor.execute(
            #     f"CREATE INDEX IF NOT EXISTS idx_match_composite ON {RAW_TABLE}(season_link, home, away)"
            # )
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

    def change_primary_key(self):
        """Change primary key of RAW_TABLE from (date, home, away) to (season_link, home, away)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Step 1: Create a temporary table with the new schema
            temp_table = f"{RAW_TABLE}_temp"
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {temp_table} (
                    -- Match data
                    season_link TEXT NOT NULL,
                    report_link TEXT UNIQUE,
                    date TEXT NOT NULL,
                    home TEXT NOT NULL,
                    score TEXT,
                    away TEXT NOT NULL,
                    attendance TEXT,
                    team_stats TEXT,
                    extra_stats TEXT,
                    
                    -- Metadata
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    PRIMARY KEY (season_link, home, away)
                )
            """
            )

            # Step 2: Copy data from old table to new table
            cursor.execute(
                f"""
                INSERT OR IGNORE INTO {temp_table} 
                (season_link, report_link, date, home, score, away, attendance, team_stats, extra_stats, date_added, last_updated)
                SELECT season_link, report_link, date, home, score, away, attendance, team_stats, extra_stats, date_added, last_updated
                FROM {RAW_TABLE} WHERE season_link != ''
            """
            )

            # Step 3: Drop the old table
            cursor.execute(f"DROP TABLE {RAW_TABLE}")

            # Step 4: Rename the temporary table to the original name
            cursor.execute(f"ALTER TABLE {temp_table} RENAME TO {RAW_TABLE}")

            # Step 5: Recreate indexes
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_report_link ON {RAW_TABLE}(report_link)"
            )
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_match_composite ON {RAW_TABLE}(season_link, home, away)"
            )

            conn.commit()
            logger.info("Successfully changed primary key to (season_link, home, away)")

    def backfill_season_links(self):
        """Backfill season_link for already transformed matches"""
        try:
            update_query = f"""
                UPDATE {TRANSFORMED_TABLE} 
                SET season_link = (
                    SELECT r.season_link 
                    FROM {RAW_TABLE} r 
                    WHERE r.report_link = {TRANSFORMED_TABLE}.report_link
                )
                WHERE season_link IS NULL OR season_link = ''
            """

            result = self.execute_query(update_query)
            logger.info(f"Backfilled season_link for transformed matches")

        except Exception as e:
            logger.error(f"Error backfilling season_links: {e}")

    def get_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Execute a SQL query and return the results as a pandas DataFrame.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for parameterized query

        Returns:
            pd.DataFrame: Query results as a DataFrame
        """
        try:
            with self.get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)
                logger.debug(f"Successfully fetched DataFrame with shape: {df.shape}")
                return df

        except Exception as e:
            logger.error(f"Error fetching DataFrame: {e}")
            # Return empty DataFrame on error
            return pd.DataFrame()
