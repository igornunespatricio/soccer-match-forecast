from database import DatabaseManager
from scraper import SerieAScraper
from config import URLS
from webdriver import ChromeDriverWrapper
from transform import DataTransformer


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
    main(scrape_basic_match_data=False, scrape_match_reports=False, transform_data=True)
