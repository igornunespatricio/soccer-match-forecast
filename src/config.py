from pathlib import Path

# ==========================================================================
# Path definitons
# ==========================================================================
DATABASE_PATH = Path(__file__).parent.parent / "data"
SCRAPER_LOGGER_PATH = Path(__file__).parent.parent / "logs" / "scraper.log"

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
