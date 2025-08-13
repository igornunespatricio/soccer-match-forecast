from scraper import SerieAScraper
from webdriver import ChromeDriverWrapper
from config import RAW_DATA_PATH, YEARS


def main():
    # Ensure data directory exists
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        for year in YEARS:
            try:
                logger.info(f"Starting scrape for year {year}")
                scraper = SerieAScraper(driver, year)

                # Scrape all matches for the year (automatically respects rate limits)
                scraper.scrape_season()

                # Save to year-specific CSV file
                filename = RAW_DATA_PATH / f"serie_a_{year}.csv"
                scraper.save_to_csv(filename)

                logger.info(
                    f"Successfully scraped {len(scraper.matches)} matches for {year}"
                )

            except Exception as e:
                logger.error(f"Error scraping year {year}: {e}")
                continue

    finally:
        driver_manager.close()
        logger.info("Scraping completed")


if __name__ == "__main__":
    # Initialize logger (imported from your logger.py)
    from logger import get_logger

    logger = get_logger("MainScraper")

    main()
