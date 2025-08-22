from dataclasses import dataclass
from database import DatabaseManager
from config import RAW_TABLE, TRANSFORMED_TABLE
from logger import get_logger
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

logger = get_logger("Transformer")


@dataclass
class Match:
    # Original match data
    date: date
    home: str
    home_score: int
    away_score: int
    away: str
    report_link: str
    attendance: Optional[int] = None

    # Transformed team stats
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_passes_attempts: Optional[int] = None
    home_passes_completed: Optional[int] = None
    away_passes_attempts: Optional[int] = None
    away_passes_completed: Optional[int] = None
    home_shots_attempts: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_attempts: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_saves_attempts: Optional[int] = None
    home_saves_completed: Optional[int] = None
    away_saves_attempts: Optional[int] = None
    away_saves_completed: Optional[int] = None

    # Transformed extra stats
    home_fouls: Optional[int] = None
    away_fouls: Optional[int] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_crosses: Optional[int] = None
    away_crosses: Optional[int] = None
    home_touches: Optional[int] = None
    away_touches: Optional[int] = None
    home_tackles: Optional[int] = None
    away_tackles: Optional[int] = None
    home_interceptions: Optional[int] = None
    away_interceptions: Optional[int] = None
    home_aerials_won: Optional[int] = None
    away_aerials_won: Optional[int] = None
    home_clearances: Optional[int] = None
    away_clearances: Optional[int] = None
    home_offsides: Optional[int] = None
    away_offsides: Optional[int] = None
    home_goal_kicks: Optional[int] = None
    away_goal_kicks: Optional[int] = None
    home_throw_ins: Optional[int] = None
    away_throw_ins: Optional[int] = None
    home_long_balls: Optional[int] = None
    away_long_balls: Optional[int] = None

    # Metadata
    date_added: Optional[datetime] = field(default_factory=datetime.now)
    last_updated: Optional[datetime] = field(default_factory=datetime.now)

    def update_stats(self, team_stats: dict, extra_stats: dict):
        """Update the match instance with team and extra stats"""
        for key, value in {**team_stats, **extra_stats}.items():
            if hasattr(self, key):
                setattr(self, key, value)


class DataTransformer:
    def __init__(self):
        self.db = DatabaseManager()

    def _raw_match_generator(self):
        """Generate raw match data from database"""
        raw_matches = self.db.execute_query(
            f"""
            SELECT * FROM {RAW_TABLE}
            WHERE date IS NOT NULL
            AND home IS NOT NULL
            AND away IS NOT NULL
            AND score IS NOT NULL
            AND report_link IS NOT NULL
            AND team_stats IS NOT NULL
            AND extra_stats IS NOT NULL
        """
        )
        for match in raw_matches:
            yield match

    def _extract_basic_match_data(self, raw_match) -> Match:
        """Extract basic match data from raw table"""
        date = raw_match["date"]
        home = raw_match["home"]
        home_score = int(raw_match["score"].split("–")[0].strip())
        away_score = int(raw_match["score"].split("–")[1].strip())
        away = raw_match["away"]
        report_link = raw_match["report_link"]
        attendance = raw_match["attendance"]
        return Match(date, home, home_score, away_score, away, report_link, attendance)

    # TODO: implement team stats
    def _extract_team_stats_data(self, raw_match) -> dict:
        """Extract team stats data from raw table"""
        return {}

    # TODO: implement extra stats
    def _extract_extra_stats_data(self, raw_match) -> dict:
        return {}

    def _save_transformed_data(self, match) -> None:
        """Save transformed match data to database"""
        self.db.execute_query(
            f"""
            INSERT INTO {TRANSFORMED_TABLE} (date, home, home_score, away_score, away, report_link, attendance, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (report_link) DO UPDATE SET
                date = excluded.date,
                home = excluded.home,
                away = excluded.away,
                home_score = excluded.home_score,
                away_score = excluded.away_score,
                report_link = excluded.report_link,
                attendance = excluded.attendance,
                last_updated = CURRENT_TIMESTAMP
            """,
            (
                match.date,
                match.home,
                match.home_score,
                match.away_score,
                match.away,
                match.report_link,
                match.attendance,
                match.last_updated,
            ),
        )

    def transform(self) -> None:
        """Transform raw match data into transformed match data"""
        for i, raw_match in enumerate(self._raw_match_generator()):
            match = self._extract_basic_match_data(raw_match)
            team_stats = self._extract_team_stats_data(raw_match)
            extra_stats = self._extract_extra_stats_data(raw_match)
            match.update_stats(team_stats, extra_stats)
            self._save_transformed_data(match)
            if i >= 0:
                break


if __name__ == "__main__":
    transformer = DataTransformer()
    transformer.transform()
