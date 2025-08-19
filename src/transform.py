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
        """Initialize the transformed table with all columns"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DROP TABLE IF EXISTS {TRANSFORMED_TABLE}"
            )  # Clear existing table
            cursor.execute(
                f"""
                CREATE TABLE {TRANSFORMED_TABLE} (
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
                    
                    -- Passing
                    home_passes_completed INTEGER,
                    home_passes_attempted INTEGER,
                    away_passes_completed INTEGER,
                    away_passes_attempted INTEGER,
                    
                    -- Shots
                    home_shots_on_target INTEGER,
                    home_shots_attempted INTEGER,
                    away_shots_on_target INTEGER,
                    away_shots_attempted INTEGER,
                    
                    -- Saves
                    home_saves_made INTEGER,
                    home_saves_attempted INTEGER,
                    away_saves_made INTEGER,
                    away_saves_attempted INTEGER,
                    
                    -- Extra stats
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
                    data_source TEXT,
                    load_id TEXT,
                    checksum TEXT,
                    version INTEGER,
                    last_updated TIMESTAMP,
                    
                    PRIMARY KEY (report_link)
                )
                """
            )
            conn.commit()
            logger.info(f"Initialized {TRANSFORMED_TABLE}")

    @staticmethod
    def parse_score(score_str: str) -> tuple:
        """Parse score string into home and away scores"""
        if not score_str:
            return None, None
        try:
            home, away = re.split(r"[-–:]", score_str.strip())
            return int(home), int(away)
        except (ValueError, AttributeError):
            return None, None

    @staticmethod
    def parse_attendance(attendance_str: str) -> int:
        """Convert attendance string to integer"""
        if not attendance_str:
            return None
        try:
            return int(re.sub(r"[^\d]", "", attendance_str))
        except ValueError:
            return None

    @staticmethod
    def parse_team_stats(team_stats_str: str) -> dict:
        """Robust team stats parser that handles malformed data"""
        if not team_stats_str or team_stats_str.strip() in ("", "null"):
            return {}

        result = {}

        # Extract possession
        poss_match = re.search(
            r"'Possession':\s*{'home':\s*'(\d+)%',\s*'away':\s*'(\d+)%'}",
            team_stats_str,
        )
        if poss_match:
            result.update(
                {
                    "home_possession": float(poss_match.group(1)),
                    "away_possession": float(poss_match.group(2)),
                }
            )

        # Extract passing accuracy
        pass_match = re.search(
            r"'Passing Accuracy':\s*{'home':\s*'[^']*?(\d+)\s*of\s*(\d+)[^']*',\s*'away':\s*'[^']*?(\d+)\s*of\s*(\d+)[^']*'}",
            team_stats_str,
        )
        if pass_match:
            result.update(
                {
                    "home_passes_completed": int(pass_match.group(1)),
                    "home_passes_attempted": int(pass_match.group(2)),
                    "away_passes_completed": int(pass_match.group(3)),
                    "away_passes_attempted": int(pass_match.group(4)),
                }
            )

        # Extract shots on target
        shots_match = re.search(
            r"'Shots on Target':\s*{'home':\s*'[^']*?(\d+)\s*of\s*(\d+)[^']*',\s*'away':\s*'[^']*?(\d+)\s*of\s*(\d+)[^']*'}",
            team_stats_str,
        )
        if shots_match:
            result.update(
                {
                    "home_shots_on_target": int(shots_match.group(1)),
                    "home_shots_attempted": int(shots_match.group(2)),
                    "away_shots_on_target": int(shots_match.group(3)),
                    "away_shots_attempted": int(shots_match.group(4)),
                }
            )

        # Extract saves
        saves_match = re.search(
            r"'Saves':\s*{'home':\s*'[^']*?(\d+)\s*of\s*(\d+)[^']*',\s*'away':\s*'[^']*?(\d+)\s*of\s*(\d+)[^']*'}",
            team_stats_str,
        )
        if saves_match:
            result.update(
                {
                    "home_saves_made": int(saves_match.group(1)),
                    "home_saves_attempted": int(saves_match.group(2)),
                    "away_saves_made": int(saves_match.group(3)),
                    "away_saves_attempted": int(saves_match.group(4)),
                }
            )

        return result

    @staticmethod
    def parse_extra_stats(extra_stats_str: str) -> dict:
        """Parse pipe-delimited extra stats with better error handling"""
        if not extra_stats_str or extra_stats_str.strip() in ("", "N/A"):
            return {}

        try:
            # Clean and split the string
            parts = [p.strip() for p in extra_stats_str.split("|") if p.strip()]

            # The format alternates between value and stat name
            stats = {}
            i = 0
            while i < len(parts) - 1:
                try:
                    # Current part should be a number (home value)
                    home_val = int(parts[i])
                    # Next part is the stat name
                    stat_name = parts[i + 1].lower().replace(" ", "_")
                    # Part after that is away value (if exists)
                    away_val = int(parts[i + 2]) if i + 2 < len(parts) else 0

                    stats.update(
                        {f"home_{stat_name}": home_val, f"away_{stat_name}": away_val}
                    )
                    i += 3  # Move to next stat group
                except (ValueError, IndexError):
                    # If parsing fails, skip to next potential stat group
                    i += 1

            return stats
        except Exception as e:
            logger.error(f"Error parsing extra stats: {str(e)}")
            return {}

    def transform_match(self, raw_match: dict) -> Optional[dict]:
        """Transform raw match data into structured format"""
        try:
            # Basic info
            home_score, away_score = self.parse_score(raw_match.get("score", ""))
            attendance = self.parse_attendance(raw_match.get("attendance", ""))

            # Stats
            team_stats = self.parse_team_stats(raw_match.get("team_stats", ""))
            extra_stats = self.parse_extra_stats(raw_match.get("extra_stats", ""))

            return {
                "date": raw_match.get("date"),
                "home_team": raw_match.get("home"),
                "away_team": raw_match.get("away"),
                "home_score": home_score,
                "away_score": away_score,
                "attendance": attendance,
                "report_link": raw_match.get("report_link"),
                **team_stats,
                **extra_stats,
                "date_added": raw_match.get("date_added"),
                "data_source": raw_match.get("data_source"),
                "load_id": raw_match.get("load_id"),
                "checksum": raw_match.get("checksum"),
                "version": raw_match.get("version"),
                "last_updated": raw_match.get("last_updated"),
            }
        except Exception as e:
            logger.error(f"Error transforming match: {str(e)}")
            return None

    def transform_all_matches(self):
        """Transform and load all matches from raw table"""
        logger.info("Starting full transformation of all matches")

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {RAW_TABLE}")
            raw_matches = [dict(row) for row in cursor.fetchall()]

        success = 0
        for match in raw_matches:
            transformed = self.transform_match(match)
            if transformed:
                self.save_transformed_match(transformed)
                success += 1

        logger.info(f"Transformation complete. Success: {success}/{len(raw_matches)}")
        return success

    def save_transformed_match(self, transformed: dict):
        """Save transformed match to database"""
        if not transformed:
            return

        columns = [
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "attendance",
            "report_link",
            "home_possession",
            "away_possession",
            "home_passes_completed",
            "home_passes_attempted",
            "away_passes_completed",
            "away_passes_attempted",
            "home_shots_on_target",
            "home_shots_attempted",
            "away_shots_on_target",
            "away_shots_attempted",
            "home_saves_made",
            "home_saves_attempted",
            "away_saves_made",
            "away_saves_attempted",
            "home_fouls",
            "away_fouls",
            "home_corners",
            "away_corners",
            "home_crosses",
            "away_crosses",
            "home_touches",
            "away_touches",
            "home_tackles",
            "away_tackles",
            "home_interceptions",
            "away_interceptions",
            "home_aerials_won",
            "away_aerials_won",
            "home_clearances",
            "away_clearances",
            "home_offsides",
            "away_offsides",
            "home_goal_kicks",
            "away_goal_kicks",
            "home_throw_ins",
            "away_throw_ins",
            "home_long_balls",
            "away_long_balls",
            "date_added",
            "data_source",
            "load_id",
            "checksum",
            "version",
            "last_updated",
        ]

        values = [transformed.get(col) for col in columns]

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {TRANSFORMED_TABLE} ({",".join(columns)})
                VALUES ({",".join(["?"]*len(columns))})
                """,
                values,
            )
            conn.commit()

    def test_transform_10_rows(self):
        """Test transformation with 10 sample rows"""
        logger.info("Starting test transformation of 10 rows")

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {RAW_TABLE} LIMIT 10")
            raw_matches = [dict(row) for row in cursor.fetchall()]

        success = 0
        for match in raw_matches:
            transformed = self.transform_match(match)
            if transformed:
                self.save_transformed_match(transformed)
                logger.info(
                    f"Transformed: {transformed['home_team']} {transformed['home_score']}-"
                    f"{transformed['away_score']} {transformed['away_team']}"
                )
                success += 1

        logger.info(f"Test complete. Success: {success}/{len(raw_matches)}")
        return success


if __name__ == "__main__":
    transformer = DataTransformer()

    # Run either test or full transformation
    transformer.test_transform_10_rows()
    # transformer.transform_all_matches()
