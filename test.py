from src.data.database import DatabaseManager
from src.config import TRANSFORMED_TABLE

db = DatabaseManager()

# delete row with report_link https://fbref.com/en/matches/3014cdf2/Sao-Paulo-Sport-Recife-March-29-2025-Serie-A

db.execute_query(
    f"DELETE FROM {TRANSFORMED_TABLE} WHERE report_link = ?",
    (
        "https://fbref.com/en/matches/3014cdf2/Sao-Paulo-Sport-Recife-March-29-2025-Serie-A",
    ),
)
