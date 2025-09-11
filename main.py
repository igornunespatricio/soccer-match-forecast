from src.data.database import DatabaseManager
from src.scraper.scraper import SerieAScraper

from src.config import URLS
from src.scraper.webdriver import ChromeDriverWrapper
from src.transform import DataTransformer


def main(
    scrape_basic_match_data: bool = True,
    scrape_match_reports: bool = True,
    transform_data: bool = True,
):
    # Initialize database
    db = DatabaseManager()
    db.initialize_db()

    # Initialize driver
    if scrape_basic_match_data or scrape_match_reports:
        driver_manager = ChromeDriverWrapper(headless=True)
        driver = driver_manager.get_driver()

        scraper = SerieAScraper(driver)

        # Scrape basic match data
        if scrape_basic_match_data:
            for url in URLS:
                scraper.scrape_basic_match_data(url=url)

        # Scrape match reports
        if scrape_match_reports:
            scraper.scrape_match_reports()

        driver_manager.close()

    if transform_data:
        transformer = DataTransformer()
        transformer.transform()


if __name__ == "__main__":
    main(scrape_basic_match_data=True, scrape_match_reports=True, transform_data=True)
