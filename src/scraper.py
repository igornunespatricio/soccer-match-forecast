import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from database import DatabaseManager
from webdriver import ChromeDriverWrapper
from logger import get_logger
from config import REQUEST_DELAY, URLS, RAW_TABLE

logger = get_logger("SerieAScraper")


@dataclass
class Match:
    date: str
    home: str
    score: str
    away: str
    attendance: str
    report_link: str
    team_stats: str
    team_stats_extra: str


class SerieAScraper:
    def __init__(self, driver, url: str):
        self.driver = driver
        self.url = url
        self.db = DatabaseManager()

    def scrape_basic_match_data(self):
        """Scrape and save to database"""
        soup = self._get_page(self.url)
        rows = soup.select(
            "table.stats_table tbody tr[data-row]:not(.spacer.partial_table.result_all, .thead)"
        )
        logger.info(f"Found {len(rows)} matches to scrape")
        for row in rows:

            if match := self._extract_match_data(row):
                print(match)
                self.db.execute_query(
                    f"INSERT OR IGNORE INTO {RAW_TABLE} (date, home, score, away, attendance, report_link) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        match["date"],
                        match["home"],
                        match["score"],
                        match["away"],
                        match["attendance"],
                        match["report_link"],
                    ),
                )
                logger.info(
                    f"Saved {match['home']} {match['score']} {match['away']} to database - {match['report_link']}"
                )

    def _get_page(self, url: str) -> BeautifulSoup:
        """Load page with configured delay"""
        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table"))
        )
        logger.debug(f"Waiting {REQUEST_DELAY:.1f}s after request")
        time.sleep(REQUEST_DELAY)
        return BeautifulSoup(self.driver.page_source, "html.parser")

    def _extract_match_data(self, row) -> Optional[Dict]:
        """Extract basic match info from schedule row"""

        def clean_text(text):
            """Remove leading and trailing spaces and return None if text is empty"""
            text = text.strip()
            return text if text != "" else None

        date = clean_text(row.select_one("td[data-stat='date']").text)
        home = clean_text(row.select_one("td[data-stat='home_team']").text)
        score = clean_text(row.select_one("td[data-stat='score']").text)
        away = clean_text(row.select_one("td[data-stat='away_team']").text)
        attendance = clean_text(row.select_one("td[data-stat='attendance']").text)
        report_link = row.select_one('td[data-stat="match_report"] a')
        if report_link and "/en/matches/" in report_link["href"]:
            report_link = f'https://fbref.com{report_link["href"]}'
        else:
            report_link = None
        results = {
            "date": date,
            "home": home,
            "score": score,
            "away": away,
            "attendance": attendance,
            "report_link": report_link,
        }
        return results

    def _extract_stats(self, soup: BeautifulSoup) -> tuple:
        """Extract team stats text from match report"""
        pass

    def scrape_match_reports(self):
        """Scrape match reports and save to database"""
        # query the database to get report links with no team_stats or extra_stats
        matches = self.db.execute_query(
            f"SELECT * FROM {RAW_TABLE} WHERE report_link IS NOT NULL AND team_stats IS NULL AND extra_stats IS NULL"
        )
        count = 0
        for match in matches:
            report_link = match["report_link"]
            print(report_link)
            count += 1
            if count >= 3:
                break


if __name__ == "__main__":
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        scraper = SerieAScraper(driver, url=URLS[0])
        # scraper.scrape_basic_match_data()
        scraper.scrape_match_reports()

    finally:
        driver_manager.close()
