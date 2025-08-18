import datetime
import sqlite3
import json
from contextlib import contextmanager
import time
from config import DATABASE_CONFIG, RAW_DATA_PATH, RAW_TABLE
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

    def initialize_db(self):
        """Create table with all lowercase column names"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
                    -- Match data
                    date TEXT,
                    home TEXT,
                    score TEXT,
                    away TEXT,
                    attendance TEXT,
                    report_link TEXT UNIQUE,
                    team_stats TEXT,
                    extra_stats TEXT,
                    
                    -- Metadata
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_source TEXT DEFAULT 'fbref_scraper',
                    load_id TEXT,
                    is_current BOOLEAN DEFAULT TRUE,
                    checksum TEXT,
                    version INTEGER DEFAULT 1,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_report_link ON {RAW_TABLE}(report_link)"
            )
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_date_added ON {RAW_TABLE}(date_added)"
            )
            conn.commit()

    def save_match(
        self, match: dict, load_id: str = None, preserve_stats: bool = False
    ):
        """Save match data with lowercase fields"""
        import hashlib

        # Convert all keys to lowercase
        match = {k.lower(): v for k, v in match.items()}

        # Prepare data with defaults
        data = {
            "date": match.get("date", ""),
            "home": match.get("home", ""),
            "away": match.get("away", ""),
            "score": match.get("score", ""),
            "attendance": match.get("attendance", ""),
            "report_link": match.get("report_link", ""),
            "team_stats": match.get("team_stats", ""),
            "extra_stats": match.get("extra_stats", "N/A"),
        }

        # Generate checksum
        checksum = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if preserve_stats:
                # Only update basic fields, preserve stats if they exist
                cursor.execute(
                    f"""
                    INSERT INTO {RAW_TABLE} (
                        date, home, away, score, attendance,
                        report_link, team_stats, extra_stats,
                        load_id, checksum
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(report_link) DO UPDATE SET
                        date = excluded.date,
                        home = excluded.home,
                        away = excluded.away,
                        score = excluded.score,
                        attendance = excluded.attendance,
                        checksum = excluded.checksum,
                        last_updated = CURRENT_TIMESTAMP,
                        is_current = TRUE
                        WHERE {RAW_TABLE}.team_stats = '' OR {RAW_TABLE}.team_stats IS NULL 
                        OR {RAW_TABLE}.extra_stats = '' OR {RAW_TABLE}.extra_stats = 'N/A'
                    """,
                    (
                        data["date"],
                        data["home"],
                        data["away"],
                        data["score"],
                        data["attendance"],
                        data["report_link"],
                        data["team_stats"],
                        data["extra_stats"],
                        load_id
                        or f"load_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        checksum,
                    ),
                )
            else:
                # Original behavior - update all fields
                cursor.execute(
                    f"""
                    INSERT INTO {RAW_TABLE} (
                        date, home, away, score, attendance,
                        report_link, team_stats, extra_stats,
                        load_id, checksum
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(report_link) DO UPDATE SET
                        date = excluded.date,
                        home = excluded.home,
                        away = excluded.away,
                        score = excluded.score,
                        attendance = excluded.attendance,
                        team_stats = excluded.team_stats,
                        extra_stats = excluded.extra_stats,
                        checksum = excluded.checksum,
                        last_updated = CURRENT_TIMESTAMP,
                        is_current = TRUE
                    """,
                    (
                        data["date"],
                        data["home"],
                        data["away"],
                        data["score"],
                        data["attendance"],
                        data["report_link"],
                        data["team_stats"],
                        data["extra_stats"],
                        load_id
                        or f"load_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        checksum,
                    ),
                )
            conn.commit()

    def migrate_csv(self, csv_path: str, batch_size: int = 50):
        """Migrate CSV data with case normalization"""
        import pandas as pd

        logger.info(f"Starting migration from {csv_path}")
        start_time = time.time()

        try:
            # Read CSV and normalize column names
            df = pd.read_csv(csv_path, keep_default_na=False, dtype=str)
            df.columns = df.columns.str.lower().str.replace(" ", "_")
            logger.info(f"Detected columns: {list(df.columns)}")

            # Process in batches
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i : i + batch_size]
                for _, row in batch.iterrows():
                    try:
                        self.save_match(row.to_dict())
                    except Exception as e:
                        logger.error(f"Failed row {i}: {str(e)}")
                        logger.debug(f"Row data: {dict(row)}")
                        continue

                # Log progress
                processed = min(i + batch_size, len(df))
                logger.info(
                    f"Progress: {processed}/{len(df)} " f"({processed/len(df):.1%})"
                )

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise

        logger.info(
            f"Migration completed in {time.time() - start_time:.1f} seconds. "
            f"Total records: {len(df)}"
        )

    def get_matches(
        self,
        year: str = None,
        has_report_link: bool = True,
        has_team_stats: bool = False,
        has_extra_stats: bool = False,
        limit: int = None,
    ) -> list[dict]:
        """
        Get matches with optional filters
        Args:
            year: Filter by year (extracted from date field)
            has_team_stats: True=has stats, False=no stats, None=don't care
            has_report_link: True=has link, False=no link, None=don't care
            has_extra_stats: True=has extra stats, False=no extra stats, None=don't care
            limit: Maximum number of matches to return
        """
        query = f"SELECT * FROM {RAW_TABLE}"
        conditions = []
        params = []

        if year:
            conditions.append("date LIKE ?")
            params.append(f"{year}%")

        if has_team_stats is not None:
            if has_team_stats:
                conditions.append(
                    "(team_stats IS NOT NULL AND team_stats != '' AND team_stats != 'null')"
                )
            else:
                conditions.append(
                    "(team_stats IS NULL OR team_stats = '' OR team_stats = 'null')"
                )

        if has_report_link is not None:
            if has_report_link:
                conditions.append("(report_link IS NOT NULL AND report_link != '')")
            else:
                conditions.append("(report_link IS NULL OR report_link = '')")

        if has_extra_stats is not None:
            if has_extra_stats:
                conditions.append(
                    "(extra_stats IS NOT NULL AND extra_stats != '' AND extra_stats != 'N/A')"
                )
            else:
                conditions.append(
                    "(extra_stats IS NULL OR extra_stats = '' OR extra_stats = 'N/A')"
                )

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if limit:
            query += f" LIMIT {limit}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    db = DatabaseManager()
    db.initialize_db()

    # testing get matches
    matches = db.get_matches(
        year="2024", has_team_stats=True, has_report_link=True, has_extra_stats=True
    )
    print("Number of matches scraped: ", len(matches))
