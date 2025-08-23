from database import DatabaseManager
from scraper import SerieAScraper
from config import URLS
from webdriver import ChromeDriverWrapper


def main(scrape_basic_match_data: bool = True, scrape_match_reports: bool = True):
    # Initialize database
    db = DatabaseManager()
    db.initialize_db()

    # Initialize driver
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    # Scrape basic match data
    scraper = SerieAScraper(driver)
    if scrape_basic_match_data:
        for url in URLS:
            scraper.scrape_basic_match_data(url=url)

    # Scrape match reports
    if scrape_match_reports:
        scraper.scrape_match_reports()

    # Close driver
    driver_manager.close()


if __name__ == "__main__":
    main(scrape_basic_match_data=False, scrape_match_reports=True)
