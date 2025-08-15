import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from database import DatabaseManager
from webdriver import ChromeDriverWrapper
from logger import get_logger
from config import REQUEST_DELAY, MAX_RETRIES, RAW_DATA_PATH

logger = get_logger("SerieAScraper")


@dataclass
class Match:
    date: str
    home: str
    score: str
    away: str
    attendance: str
    report_link: str
    team_stats: Dict
    team_stats_extra: str


class SerieAScraper:
    def __init__(self, driver, year: int):
        self.driver = driver
        self.year = year
        self.db = DatabaseManager()
        self.db.initialize_db()  # Ensure tables exist

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
        if (
            not (score := row.select_one("td[data-stat='score']"))
            or not score.text.strip()
        ):
            return None

        report_link = row.select_one('td[data-stat="match_report"] a')
        return {
            "date": row.select_one("td[data-stat='date']").text.strip(),
            "home": row.select_one("td[data-stat='home_team']").text.strip(),
            "score": score.text.strip(),
            "away": row.select_one("td[data-stat='away_team']").text.strip(),
            "attendance": row.select_one("td[data-stat='attendance']").text.strip(),
            "report_link": (
                f"https://fbref.com{report_link['href']}" if report_link else None
            ),
        }

    def _extract_stats(self, soup: BeautifulSoup) -> tuple:
        """Extract team stats from match report"""
        stats = {}
        current_label = None

        if stats_div := soup.find("div", id="team_stats"):
            for row in stats_div.find_all("tr"):
                if (th := row.find("th")) and th.get("colspan") == "2":
                    current_label = th.get_text(strip=True)
                elif current_label and (tds := row.find_all("td")) and len(tds) == 2:
                    stats[current_label] = {
                        "home": tds[0].get_text(strip=True),
                        "away": tds[1].get_text(strip=True),
                    }

        extra_stats = (
            " | ".join(
                item.get_text(strip=True)
                for block in soup.find("div", id="team_stats_extra").find_all(
                    "div", recursive=False
                )
                for item in block.find_all("div")
                if "th" not in item.get("class", [])
            )
            if soup.find("div", id="team_stats_extra")
            else "N/A"
        )
        return stats, extra_stats

    def scrape_basic_match_data(self):
        """Scrape and save to database"""
        soup = self._get_page(
            f"https://fbref.com/en/comps/24/{self.year}/schedule/{self.year}-Serie-A-Scores-and-Fixtures"
        )

        for row in soup.select("table.stats_table tbody tr"):
            if match := self._extract_match_data(row):
                # Pass preserve_stats=True to keep existing stats
                self.db.save_match(match, preserve_stats=True)

        logger.info(f"Saved basic match data to database")

    def scrape_match_reports(self):
        """Process unscraped matches"""
        for match in self.db.get_all_matches():
            if not match.get("team_stats") and match.get("report_link"):
                try:
                    report_soup = self._get_page(match["report_link"])
                    team_stats, extra_stats = self._extract_stats(report_soup)

                    self.db.save_match(
                        {
                            **match,
                            "team_stats": json.dumps(team_stats),
                            "team_stats_extra": extra_stats,
                        }
                    )
                    logger.info(f"Updated stats for {match['home']} vs {match['away']}")
                except Exception as e:
                    logger.error(f"Failed to scrape {match['report_link']}: {e}")


if __name__ == "__main__":
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        scraper = SerieAScraper(driver, 2023)
        scraper.scrape_basic_match_data()
        scraper.scrape_match_reports()

    finally:
        driver_manager.close()
