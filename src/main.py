from database import DatabaseManager
from scraper import SerieAScraper
from config import URLS
from webdriver import ChromeDriverWrapper


def main():
    # Initialize database
    db = DatabaseManager()
    db.initialize_db()

    # Initialize driver
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        # Scrape and migrate data
        scraper = SerieAScraper(driver, url=URLS[0])
        scraper.scrape_basic_match_data()
        scraper.scrape_match_reports()
    finally:
        driver_manager.close()


if __name__ == "__main__":
    main()
