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
from config import REQUEST_DELAY, SCRAPER_LOGGER_PATH, URLS, RAW_TABLE

logger = get_logger("SerieAScraper", SCRAPER_LOGGER_PATH)


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
    def __init__(self, driver: ChromeDriverWrapper):
        self.driver = driver
        self.db = DatabaseManager()

    def scrape_basic_match_data(self, url: str):
        """Scrape and save to database"""
        try:
            soup = self._get_page(url)
            rows = soup.select(
                "table.stats_table tbody tr[data-row]:not(.spacer.partial_table.result_all, .thead)"
            )
            logger.info(f"Found {len(rows)} matches to scrape")
            for i, row in enumerate(rows):
                if match := self._extract_match_data(row):
                    self.db.execute_query(
                        "INSERT INTO raw_matches (date, home, score, away, attendance, report_link, last_updated) "
                        "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
                        "ON CONFLICT(date, home, away) DO UPDATE SET "
                        "score = COALESCE(score, excluded.score), "
                        "report_link = COALESCE(report_link, excluded.report_link), "
                        "attendance = excluded.attendance, "
                        "last_updated = CURRENT_TIMESTAMP "
                        "WHERE score IS NULL OR report_link IS NULL",
                        (
                            match["date"],
                            match["home"],
                            match["score"],
                            match["away"],
                            match["attendance"],
                            match["report_link"],
                        ),
                    )
                    # TODO: fix - only log if match is saved
                    logger.info(
                        f"Saved match {i+1}/{len(rows)}: {match['home']} {match['score']} {match['away']} to database - {match['report_link']}"
                    )
        except Exception as e:
            logger.error(f"Error while scraping basic match data: {e}")

    def _get_page(self, url: str) -> BeautifulSoup:
        """Load page with configured delay"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table"))
            )
            logger.debug(f"Waiting {REQUEST_DELAY:.1f}s after request")
            time.sleep(REQUEST_DELAY)
            return BeautifulSoup(self.driver.page_source, "html.parser")
        except Exception as e:
            logger.error(f"Error loading page: {e}")
        return None

    def _extract_match_data(self, row) -> Optional[Dict]:
        """Extract basic match info from schedule row"""

        def clean_text(text):
            """Remove leading and trailing spaces and return None if text is empty"""
            text = text.strip()
            return text if text != "" else None

        try:
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
        except Exception as e:
            logger.error(f"Error extracting match data: {e}")
        return None

    def _extract_team_stats(self, soup: BeautifulSoup):
        """Extract team_stats from report link"""
        try:
            team_stats_div = soup.select_one("div#team_stats")
            if team_stats_div:
                return str(team_stats_div)
        except Exception as e:
            logger.error(f"Error extracting team stats: {e}")
        return None

    def _extract_extra_stats(self, soup: BeautifulSoup):
        """Extract extra_stats from report link"""
        try:
            team_extra_stats_div = soup.select_one("div#team_stats_extra")
            if team_extra_stats_div:
                return str(team_extra_stats_div)
        except Exception as e:
            logger.error(f"Error extracting extra stats: {e}")
        return None

    def scrape_match_reports(self, year: Optional[int] = None):
        """Scrape match reports and save to database"""
        try:
            query = f"SELECT * FROM {RAW_TABLE} WHERE report_link IS NOT NULL AND team_stats IS NULL AND extra_stats IS NULL"
            if year:
                query += f" AND date LIKE '{year}%'"
            matches = self.db.execute_query(query)
            logger.info(f"Found {len(matches)} match reports to scrape")
            for i, match in enumerate(matches):
                soup = self._get_page(match["report_link"])
                team_stats = self._extract_team_stats(soup)
                extra_stats = self._extract_extra_stats(soup)

                self.db.execute_query(
                    f"UPDATE {RAW_TABLE} SET team_stats = ?, extra_stats = ?, last_updated = CURRENT_TIMESTAMP WHERE report_link = ?",
                    (team_stats, extra_stats, match["report_link"]),
                )

                logger.info(
                    f"Match {i+1}/{len(matches)} - Saved team stats and extra stats - {match['home']} {match['score']} {match['away']} - {match['report_link']}"
                )

        except Exception as e:
            logger.error(f"Error while scraping match reports: {e}")


if __name__ == "__main__":
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        scraper = SerieAScraper(driver)
        scraper.scrape_basic_match_data(url=URLS[0])
        # scraper.scrape_match_reports()

    finally:
        driver_manager.close()
