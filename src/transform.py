import json
import re
from typing import Optional
from database import DatabaseManager
from config import RAW_TABLE, TRANSFORMED_TABLE
from logger import get_logger

logger = get_logger("Transformer")


class DataTransformer:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.initialize_transformed_table()

    def initialize_transformed_table(self):
        """Initialize the transformed table with raw number columns"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TRANSFORMED_TABLE} (
                    -- Basic match info
                    date TEXT,
                    home_team TEXT,
                    away_team TEXT,
                    home_score INTEGER,
                    away_score INTEGER,
                    attendance INTEGER,
                    report_link TEXT UNIQUE,
                    
                    -- Possession
                    home_possession REAL,
                    away_possession REAL,
                    
                    -- Passing (raw numbers)
                    home_passes_completed INTEGER,
                    home_passes_attempted INTEGER,
                    away_passes_completed INTEGER,
                    away_passes_attempted INTEGER,
                    
                    -- Shots (raw numbers)
                    home_shots_on_target INTEGER,
                    home_shots_attempted INTEGER,
                    away_shots_on_target INTEGER,
                    away_shots_attempted INTEGER,
                    
                    -- Saves (raw numbers)
                    home_saves_made INTEGER,
                    home_saves_attempted INTEGER,
                    away_saves_made INTEGER,
                    away_saves_attempted INTEGER,
                    
                    -- Metadata
                    date_added TIMESTAMP,
                    data_source TEXT,
                    load_id TEXT,
                    checksum TEXT,
                    version INTEGER,
                    last_updated TIMESTAMP,
                    
                    PRIMARY KEY (report_link)
                )
                """
            )
            # Create indexes
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_transformed_date ON {TRANSFORMED_TABLE}(date)"
            )
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_transformed_teams ON {TRANSFORMED_TABLE}(home_team, away_team)"
            )
            conn.commit()
            logger.info(f"Initialized {TRANSFORMED_TABLE} with raw stats columns")

    @staticmethod
    def parse_score(score_str: str) -> tuple:
        """Parse score string into home and away scores"""
        if not score_str or score_str.strip() == "":
            return None, None

        score_parts = re.split(r"[-–:]", score_str.strip())
        if len(score_parts) != 2:
            return None, None

        try:
            return int(score_parts[0]), int(score_parts[1])
        except (ValueError, TypeError):
            return None, None

    @staticmethod
    def parse_attendance(attendance_str: str) -> int:
        """Convert attendance string to integer"""
        if not attendance_str or attendance_str.strip() == "":
            return None

        try:
            return int(re.sub(r"[^\d]", "", attendance_str.strip()))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_passing_data(passing_str: str) -> tuple:
        """Extract completed and attempted passes from string"""
        if not passing_str:
            return None, None

        # Example format: "464 of 561 —83%"
        match = re.search(r"(\d+) of (\d+)", passing_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    @staticmethod
    def parse_shots_data(shots_str: str) -> tuple:
        """Extract shots on target and total shots from string"""
        if not shots_str:
            return None, None

        # Example format: "9 of 17 —53%"
        match = re.search(r"(\d+) of (\d+)", shots_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    @staticmethod
    def parse_saves_data(saves_str: str) -> tuple:
        """Extract saves made and save opportunities from string"""
        if not saves_str:
            return None, None

        # Example format: "3 of 4 —75%"
        match = re.search(r"(\d+) of (\d+)", saves_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def parse_team_stats(self, team_stats_str: str) -> dict:
        """Parse the team stats JSON into raw numbers"""
        if not team_stats_str or team_stats_str.strip() in ("", "null"):
            return {}

        try:
            stats = json.loads(team_stats_str)
            parsed = {}

            # Possession (keep percentages)
            if "Possession" in stats:
                home_poss = stats["Possession"].get("home", "0%").strip("%")
                away_poss = stats["Possession"].get("away", "0%").strip("%")
                parsed.update(
                    {
                        "home_possession": float(home_poss) if home_poss else 0.0,
                        "away_possession": float(away_poss) if away_poss else 0.0,
                    }
                )

            # Passing (raw numbers)
            if "Passing Accuracy" in stats:
                home_pass = stats["Passing Accuracy"].get("home", "")
                away_pass = stats["Passing Accuracy"].get("away", "")

                home_completed, home_attempted = self.parse_passing_data(home_pass)
                away_completed, away_attempted = self.parse_passing_data(away_pass)

                parsed.update(
                    {
                        "home_passes_completed": home_completed or 0,
                        "home_passes_attempted": home_attempted or 0,
                        "away_passes_completed": away_completed or 0,
                        "away_passes_attempted": away_attempted or 0,
                    }
                )

            # Shots (raw numbers)
            if "Shots on Target" in stats:
                home_shots = stats["Shots on Target"].get("home", "")
                away_shots = stats["Shots on Target"].get("away", "")

                home_on_target, home_attempted = self.parse_shots_data(home_shots)
                away_on_target, away_attempted = self.parse_shots_data(away_shots)

                parsed.update(
                    {
                        "home_shots_on_target": home_on_target or 0,
                        "home_shots_attempted": home_attempted or 0,
                        "away_shots_on_target": away_on_target or 0,
                        "away_shots_attempted": away_attempted or 0,
                    }
                )

            # Saves (raw numbers)
            if "Saves" in stats:
                home_saves = stats["Saves"].get("home", "")
                away_saves = stats["Saves"].get("away", "")

                home_made, home_attempted = self.parse_saves_data(home_saves)
                away_made, away_attempted = self.parse_saves_data(away_saves)

                parsed.update(
                    {
                        "home_saves_made": home_made or 0,
                        "home_saves_attempted": home_attempted or 0,
                        "away_saves_made": away_made or 0,
                        "away_saves_attempted": away_attempted or 0,
                    }
                )

            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse team stats: {str(e)}")
            return {}

    def transform_match(self, raw_match: dict) -> Optional[dict]:
        """Transform match data with raw numbers"""
        try:
            # Basic info
            home_score, away_score = self.parse_score(raw_match.get("score", ""))
            attendance = self.parse_attendance(raw_match.get("attendance", ""))
            team_stats = self.parse_team_stats(raw_match.get("team_stats", ""))

            transformed = {
                # Basic match info
                "date": raw_match.get("date"),
                "home_team": raw_match.get("home"),
                "away_team": raw_match.get("away"),
                "home_score": home_score,
                "away_score": away_score,
                "attendance": attendance,
                "report_link": raw_match.get("report_link"),
                # Team stats (raw numbers)
                **team_stats,
                # Metadata
                "date_added": raw_match.get("date_added"),
                "data_source": raw_match.get("data_source"),
                "load_id": raw_match.get("load_id"),
                "checksum": raw_match.get("checksum"),
                "version": raw_match.get("version"),
                "last_updated": raw_match.get("last_updated"),
            }
            return transformed
        except Exception as e:
            logger.error(
                f"Failed to transform match {raw_match.get('report_link')}: {str(e)}"
            )
            return None

    def save_transformed_match(self, transformed_match: dict):
        """Save transformed match with raw stats"""
        if not transformed_match:
            return

        columns = [
            # Basic info
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "attendance",
            "report_link",
            # Possession
            "home_possession",
            "away_possession",
            # Passing
            "home_passes_completed",
            "home_passes_attempted",
            "away_passes_completed",
            "away_passes_attempted",
            # Shots
            "home_shots_on_target",
            "home_shots_attempted",
            "away_shots_on_target",
            "away_shots_attempted",
            # Saves
            "home_saves_made",
            "home_saves_attempted",
            "away_saves_made",
            "away_saves_attempted",
            # Metadata
            "date_added",
            "data_source",
            "load_id",
            "checksum",
            "version",
            "last_updated",
        ]

        placeholders = ", ".join(["?"] * len(columns))
        values = [transformed_match.get(col) for col in columns]

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {TRANSFORMED_TABLE} ({", ".join(columns)})
                VALUES ({placeholders})
                """,
                values,
            )
            conn.commit()

    def test_transform_10_rows(self):
        """Test transformation with 10 rows showing raw numbers"""
        logger.info("Starting test transformation of 10 rows (raw numbers)...")

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {RAW_TABLE} ORDER BY date LIMIT 10")
            raw_matches = [dict(row) for row in cursor.fetchall()]

        if not raw_matches:
            logger.warning("No raw matches found for testing")
            return 0

        success_count = 0
        for i, raw_match in enumerate(raw_matches, 1):
            transformed = self.transform_match(raw_match)
            if transformed:
                self.save_transformed_match(transformed)
                logger.info(
                    f"Row {i}: {transformed['home_team']} {transformed['home_score']}-"
                    f"{transformed['away_score']} {transformed['away_team']}\n"
                    f"Passes: {transformed['home_passes_completed']}/{transformed['home_passes_attempted']} "
                    f"vs {transformed['away_passes_completed']}/{transformed['away_passes_attempted']}\n"
                    f"Shots: {transformed['home_shots_on_target']}/{transformed['home_shots_attempted']} "
                    f"vs {transformed['away_shots_on_target']}/{transformed['away_shots_attempted']}\n"
                    f"Saves: {transformed['home_saves_made']}/{transformed['home_saves_attempted']} "
                    f"vs {transformed['away_saves_made']}/{transformed['away_saves_attempted']}"
                )
                success_count += 1
            else:
                logger.warning(f"Failed to transform row {i}")

        logger.info(
            f"Test complete. Successfully transformed {success_count}/{len(raw_matches)} matches"
        )
        return success_count


if __name__ == "__main__":
    transformer = DataTransformer()
    transformer.test_transform_10_rows()
