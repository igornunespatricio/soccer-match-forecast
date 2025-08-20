from database import DatabaseManager


def main():
    # Initialize database
    db = DatabaseManager()
    db.initialize_db()


if __name__ == "__main__":
    main()
