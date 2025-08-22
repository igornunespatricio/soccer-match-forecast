from dataclasses import dataclass
import re
import sqlite3

from bs4 import BeautifulSoup
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
    home_shots_completed: Optional[int] = None
    away_shots_attempts: Optional[int] = None
    away_shots_completed: Optional[int] = None
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

    def _extract_basic_match_data(self, raw_match: sqlite3.Row) -> Match:
        """Extract basic match data from raw table"""
        date = raw_match["date"]
        home = raw_match["home"]
        home_score = int(raw_match["score"].split("–")[0].strip())
        away_score = int(raw_match["score"].split("–")[1].strip())
        away = raw_match["away"]
        report_link = raw_match["report_link"]
        attendance = raw_match["attendance"]
        return Match(date, home, home_score, away_score, away, report_link, attendance)

    def _extract_team_stats_data(self, raw_match: sqlite3.Row) -> dict:
        """Extract team stats data from raw table"""
        soup = BeautifulSoup(raw_match["team_stats"], "html.parser")
        team_stats = {
            **self._extract_percentage_from_team_stats(soup, "Possession"),
            **self._extract_absolute_team_stats(soup, "Passing Accuracy", "passes"),
            **self._extract_absolute_team_stats(soup, "Shots on Target", "shots"),
            **self._extract_absolute_team_stats(soup, "Saves", "saves"),
        }
        return team_stats

    def _extract_absolute_team_stats(self, soup, category, label) -> dict:
        """Extract absolute values from team stats"""
        category_dict = {}
        category_data = soup.select(
            f'div#team_stats tr:has(th:-soup-contains("{category}")) + tr'
        )
        if category_data:
            data_row = category_data[0]
            home_text = data_row.select_one("td:first-child").get_text()
            away_text = data_row.select_one("td:last-child").get_text()

            home_match = re.search(r"(\d+)\s+of\s+(\d+)", home_text)
            away_match = re.search(r"(\d+)\s+of\s+(\d+)", away_text)

            if home_match:
                category_dict[f"home_{label}_completed"] = int(home_match.group(1))
                category_dict[f"home_{label}_attempts"] = int(home_match.group(2))
            if away_match:
                category_dict[f"away_{label}_completed"] = int(away_match.group(1))
                category_dict[f"away_{label}_attempts"] = int(away_match.group(2))

        return category_dict

    def _extract_percentage_from_team_stats(self, soup, category) -> dict:
        """Extract percentage data from team stats"""
        possession_dict = {}
        possession_data = soup.select(
            f'div#team_stats tr:has(th:-soup-contains("{category}")) + tr'
        )
        if possession_data:
            data_row = possession_data[0]
            home_percent = data_row.select_one("td:first-child strong")
            away_percent = data_row.select_one("td:last-child strong")
            if home_percent and away_percent:
                try:
                    possession_dict["home_possession"] = float(
                        home_percent.get_text(strip=True).replace("%", "")
                    )
                    possession_dict["away_possession"] = float(
                        away_percent.get_text(strip=True).replace("%", "")
                    )
                except ValueError:
                    pass
        return possession_dict

    # TODO: implement extra stats
    def _extract_extra_stats_data(self, raw_match: sqlite3.Row) -> dict:
        """Extract extra stats data from raw table"""
        column_map = {
            "Fouls": ("home_fouls", "away_fouls"),
            "Corners": ("home_corners", "away_corners"),
            "Crosses": ("home_crosses", "away_crosses"),
            "Touches": ("home_touches", "away_touches"),
            "Tackles": ("home_tackles", "away_tackles"),
            "Interceptions": ("home_interceptions", "away_interceptions"),
            "Aerials Won": ("home_aerials_won", "away_aerials_won"),
            "Clearances": ("home_clearances", "away_clearances"),
            "Offsides": ("home_offsides", "away_offsides"),
            "Goal Kicks": ("home_goal_kicks", "away_goal_kicks"),
            "Throw Ins": ("home_throw_ins", "away_throw_ins"),
            "Long Balls": ("home_long_balls", "away_long_balls"),
        }

        def clean_item(div):
            text = div.get_text().strip().lower().replace(" ", "_")
            return text

        soup = BeautifulSoup(raw_match["extra_stats"], "html.parser")
        data_divs = soup.select("div#team_stats_extra > div > div:not([class])")
        home_data = [clean_item(div) for div in data_divs[::3]]
        stat_name = [clean_item(div) for div in data_divs[1::3]]
        away_data = [clean_item(div) for div in data_divs[2::3]]
        print(home_data)
        print(stat_name)
        print(away_data)
        return {}

    def _save_transformed_data(self, match: Match) -> None:
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
            # team_stats = self._extract_team_stats_data(raw_match)
            extra_stats = self._extract_extra_stats_data(raw_match)
            print(extra_stats)
            # if team_stats and extra_stats:
            #     match.update_stats(team_stats, extra_stats)

            # self._save_transformed_data(match)
            if i >= 0:
                break


if __name__ == "__main__":
    transformer = DataTransformer()
    transformer.transform()
