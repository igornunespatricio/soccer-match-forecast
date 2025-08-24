from pathlib import Path

# ==========================================================================
# Path definitons
# ==========================================================================
DATABASE_PATH = Path(__file__).parent.parent / "data"
SCRAPER_LOGGER_PATH = Path(__file__).parent.parent / "logs" / "scraper.log"
TRANSFORMER_LOGGER_PATH = Path(__file__).parent.parent / "logs" / "transformer.log"
# ==========================================================================
# Web Scraper Configuration
# ==========================================================================
# Define the URL of the page to scrape
URLS = [
    "https://fbref.com/en/comps/24/2025/schedule/2025-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2024/schedule/2024-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2023/schedule/2023-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2022/schedule/2022-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2021/schedule/2021-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2020/schedule/2020-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2019/schedule/2019-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2018/schedule/2018-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2017/schedule/2017-Serie-A-Scores-and-Fixtures",
    "https://fbref.com/en/comps/24/2016/schedule/2016-Serie-A-Scores-and-Fixtures",
]

# Define request delay and max retries for web requests
REQUEST_DELAY = 7
MAX_RETRIES = 3

# ==========================================================================
# Database Configuration
# ==========================================================================
DATABASE_CONFIG = {
    "engine": "sqlite",  # Change to 'postgresql' for PostgreSQL
    "sqlite_path": DATABASE_PATH / "matches.db",  # SQLite file path
    "postgresql": {  # Only needed if using PostgreSQL
        "host": "localhost",
        "port": 5432,
        "database": "seriea",
        "user": "postgres",
        "password": "yourpassword",
    },
}
RAW_TABLE = "raw_matches"
TRANSFORMED_TABLE = "transformed_matches"

TRANSFORMED_COLUMNS = [
    "date",
    "home",
    "home_score",
    "away_score",
    "away",
    "attendance",
    "report_link",
    "home_possession",
    "away_possession",
    "home_passes_attempts",
    "home_passes_completed",
    "away_passes_attempts",
    "away_passes_completed",
    "home_shots_attempts",
    "home_shots_completed",
    "away_shots_attempts",
    "away_shots_completed",
    "home_saves_attempts",
    "home_saves_completed",
    "away_saves_attempts",
    "away_saves_completed",
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
]


COLUMN_MAP = {
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

RAW_TABLE_QUERY = f"""
                CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
                    -- Match data
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

                    PRIMARY KEY (date, home, away)  -- Composite primary key
                )
                """

TRANSFOMED_TABLE_QUERY = f"""
                CREATE TABLE IF NOT EXISTS {TRANSFORMED_TABLE} (
                    -- Original match data
                    date DATE NOT NULL,
                    home TEXT NOT NULL,
                    home_score INT NOT NULL,
                    away_score INT NOT NULL,
                    away TEXT NOT NULL,
                    attendance INT,
                    report_link TEXT NOT NULL UNIQUE,
                    
                    -- Transformed team stats
                    home_possession REAL,
                    away_possession REAL,
                    home_passes_attempts INTEGER,
                    home_passes_completed INTEGER,
                    away_passes_attempts INTEGER,
                    away_passes_completed INTEGER,
                    home_shots_attempts INTEGER,
                    home_shots_completed INTEGER,
                    away_shots_attempts INTEGER,
                    away_shots_completed INTEGER,
                    home_saves_attempts INTEGER,
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
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    PRIMARY KEY (report_link)
                )
                """
