from src.config import URLS, RAW_DATA_PATH
from src.match_scraper import SerieAScraper


def main():
    print("🚀 Starting Série A match scraper...")

    for year, url in URLS.items():
        output_file = RAW_DATA_PATH / f"serie_a_matches_{year}.csv"
        print(f"📅 Scraping {year} season...")
        scraper = SerieAScraper(url=str(url))
        scraper.scrape()
        scraper.save_to_csv(output_path=str(output_file))

    print("✅ All seasons scraped successfully.")


if __name__ == "__main__":
    main()
