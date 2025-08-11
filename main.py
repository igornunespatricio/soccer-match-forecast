from scripts.scraper import SerieAScoreScraper


def main():
    scraper = SerieAScoreScraper(
        "https://fbref.com/en/comps/24/schedule/Serie-A-Scores-and-Fixtures"
    )
    scraper.run()


if __name__ == "__main__":
    main()
