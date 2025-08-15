from database import DatabaseManager
from config import RAW_DATA_PATH


def main():
    db = DatabaseManager()
    db.initialize_db()

    csv_path = RAW_DATA_PATH / "serie_a_2024_results.csv"
    db.migrate_csv(csv_path)


if __name__ == "__main__":
    main()
