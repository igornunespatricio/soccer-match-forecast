from dataclasses import dataclass
import re
import sqlite3

from bs4 import BeautifulSoup
from database import DatabaseManager
from config import RAW_TABLE, TRANSFORMED_TABLE, TRANSFORMED_COLUMNS, COLUMN_MAP
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

    def update_stats(self, *stat_dics):
        """Update the match data with new stats"""
        try:
            for stat_dic in stat_dics:
                for key, value in stat_dic.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception as e:
            logger.error(f"Error while updating match stats: {e}")


class DataTransformer:
    def __init__(self):
        self.db = DatabaseManager()

    def _raw_match_generator(self):
        """Generator method for raw match data"""
        try:
            raw_matches = self.db.execute_query(
                f"""
                SELECT * FROM {RAW_TABLE}
                WHERE 
                report_link NOT IN (SELECT report_link FROM {TRANSFORMED_TABLE})
                AND date IS NOT NULL
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
        except Exception as e:
            logger.error(f"Error while generating raw match data: {e}")

    def _extract_basic_match_data(self, raw_match: sqlite3.Row) -> Match:
        """Extract basic match data from raw table"""
        try:
            date = raw_match["date"]
            home = raw_match["home"]
            home_score = int(raw_match["score"].split("–")[0].strip())
            away_score = int(raw_match["score"].split("–")[1].strip())
            away = raw_match["away"]
            report_link = raw_match["report_link"]
            attendance = raw_match["attendance"]
            return Match(
                date, home, home_score, away_score, away, report_link, attendance
            )
        except Exception as e:
            logger.error(f"Error while extracting basic match data: {e}")
            return Match

    def _extract_team_stats_data(self, raw_match: sqlite3.Row) -> dict:
        """Extract team stats data from raw table"""
        try:

            soup = BeautifulSoup(raw_match["team_stats"], "html.parser")
            team_stats = {
                **self._extract_percentage_from_team_stats(
                    soup, "Possession", "possession"
                ),
                **self._extract_absolute_team_stats(soup, "Passing Accuracy", "passes"),
                **self._extract_absolute_team_stats(soup, "Shots on Target", "shots"),
                **self._extract_absolute_team_stats(soup, "Saves", "saves"),
            }
            return team_stats

        except Exception as e:
            logger.error(f"Error while extracting team stats data: {e}")
            return {}

    def _extract_absolute_team_stats(self, soup, category, label) -> dict:
        """Extract absolute values from team stats"""
        category_dict = {}
        try:
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
        except Exception as e:
            logger.error(f"Error while extracting {label} data: {e}")
            return {}

    def _extract_percentage_from_team_stats(self, soup, category, label) -> dict:
        """Extract percentage data from team stats"""
        try:
            percentage_dict = {}
            percentage_data = soup.select(
                f'div#team_stats tr:has(th:-soup-contains("{category}")) + tr'
            )
            if percentage_data:
                data_row = percentage_data[0]
                home_percent = data_row.select_one("td:first-child strong")
                away_percent = data_row.select_one("td:last-child strong")
                if home_percent and away_percent:
                    try:
                        percentage_dict[f"home_{label}"] = float(
                            home_percent.get_text(strip=True).replace("%", "")
                        )
                        percentage_dict[f"away_{label}"] = float(
                            away_percent.get_text(strip=True).replace("%", "")
                        )
                    except ValueError:
                        pass
            return percentage_dict
        except Exception as e:
            logger.error(f"Error while extracting {category} data: {e}")
            return {}

    def _extract_extra_stats_data(self, raw_match: sqlite3.Row) -> dict:
        """Extract extra stats data from raw table"""

        def clean_item(div):
            text = div.get_text().strip()
            return text

        try:

            extra_stats = {}
            soup = BeautifulSoup(raw_match["extra_stats"], "html.parser")
            data_divs = soup.select("div#team_stats_extra > div > div:not([class])")
            home_data = [clean_item(div) for div in data_divs[::3]]
            stat_names = [clean_item(div) for div in data_divs[1::3]]
            away_data = [clean_item(div) for div in data_divs[2::3]]
            for i, stat_name in enumerate(stat_names):
                if stat_name in COLUMN_MAP:
                    extra_stats[COLUMN_MAP[stat_name][0]] = int(home_data[i])
                    extra_stats[COLUMN_MAP[stat_name][1]] = int(away_data[i])
            return extra_stats

        except Exception as e:
            logger.error(f"Error while extracting extra stats data: {e}")
            return {}

    def _save_transformed_data(self, match: Match) -> None:
        """Save transformed match data to database"""
        try:
            columns = ", ".join(TRANSFORMED_COLUMNS)
            placeholders = ", ".join(["?"] * len(TRANSFORMED_COLUMNS))
            update_clause = ", ".join(
                [
                    f"{column} = excluded.{column}"
                    for column in TRANSFORMED_COLUMNS
                    if column != "report_link"
                ]
            )
            query = f"""
                INSERT INTO {TRANSFORMED_TABLE} ({columns})
                VALUES ({placeholders})
                ON CONFLICT (report_link) DO UPDATE SET
                    {update_clause},
                    last_updated = CURRENT_TIMESTAMP
            """
            self.db.execute_query(
                query,
                tuple(getattr(match, column) for column in TRANSFORMED_COLUMNS),
            )

        except Exception as e:
            logger.error(f"Error while saving transformed data: {e}")

    def transform(self) -> None:
        """Transform raw match data into transformed match data"""
        try:
            raw_matches = self._raw_match_generator()
            logger.info(f"Transforming matches...")
            for i, raw_match in enumerate(raw_matches):
                try:
                    match = self._extract_basic_match_data(raw_match)
                    team_stats = self._extract_team_stats_data(raw_match)
                    extra_stats = self._extract_extra_stats_data(raw_match)
                    match.update_stats(team_stats, extra_stats)
                    self._save_transformed_data(match)
                    logger.info(
                        f"Transformed match {i+1} - {match.home} {match.home_score} x {match.away_score} {match.away} - {match.report_link}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error while transforming match {match.report_link}: {e}"
                    )
            logger.info(f"Transformation completed!")
        except Exception as e:
            logger.error(f"Error in transformation process: {e}")


if __name__ == "__main__":
    transformer = DataTransformer()
    transformer.transform()
