from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class TransformedMatch:
    # Original match data
    season_link: str
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
        for stat_dic in stat_dics:
            for key, value in stat_dic.items():
                if hasattr(self, key):
                    setattr(self, key, value)


@dataclass
class RawMatch:
    season_link: str
    date: str
    home: str
    score: str
    away: str
    attendance: str
    report_link: str
    team_stats: str
    team_stats_extra: str
