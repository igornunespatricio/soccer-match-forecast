from pathlib import Path

# Define base directory
BASE_DIR = Path("D:/igor/projects/soccer-match-forecast")

# Define raw data path
RAW_DATA_PATH = BASE_DIR / "data" / "raw"

URLS = {
    2024: "https://fbref.com/en/comps/24/2024/schedule/2024-Serie-A-Scores-and-Fixtures",
    2025: "https://fbref.com/en/comps/24/2025/schedule/2025-Serie-A-Scores-and-Fixtures",
}
