import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver import ChromeDriverWrapper
from logger import get_logger

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
        self.matches = []
        self.request_times = []

    def _wait_if_needed(self):
        """Enforce 18 requests per minute limit"""
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]

        if len(self.request_times) >= 18:
            wait = 60 - (now - self.request_times[0]) + 1
            logger.info(f"Waiting {wait:.1f}s to comply with rate limits")
            time.sleep(wait)
            self.request_times = []

        time.sleep(random.uniform(2, 4))  # Random delay
        self.request_times.append(time.time())

    def _get_page(self, url: str) -> BeautifulSoup:
        """Load page with rate limiting"""
        self._wait_if_needed()
        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table"))
        )
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

    def scrape_season(self, max_matches=None) -> List[Match]:
        """Scrape all matches with automatic rate limiting"""
        base_url = f"https://fbref.com/en/comps/24/{self.year}/schedule/{self.year}-Serie-A-Scores-and-Fixtures"
        soup = self._get_page(base_url)

        for i, row in enumerate(soup.select("table.stats_table tbody tr")):
            if max_matches and i >= max_matches:
                break

            if not (match := self._extract_match_data(row)) or not match["report_link"]:
                continue

            try:
                report_soup = self._get_page(match["report_link"])
                team_stats, extra_stats = self._extract_stats(report_soup)

                self.matches.append(
                    Match(
                        match["date"],
                        match["home"],
                        match["score"],
                        match["away"],
                        match["attendance"],
                        match["report_link"],
                        team_stats,
                        extra_stats,
                    )
                )
                logger.info(
                    f"Scraped {i+1}: {match['home']} vs {match['away']} - Report: {match['report_link']}"
                )

            except Exception as e:
                logger.error(f"Error on match {i+1}: {e}")
                continue

        return self.matches

    def save_to_csv(self, filename):
        """Save scraped matches to CSV"""
        if not self.matches:
            logger.warning("No matches to save")
            return

        pd.DataFrame(
            [
                {
                    "Date": m.date,
                    "Home": m.home,
                    "Score": m.score,
                    "Away": m.away,
                    "Attendance": m.attendance,
                    "Report Link": m.report_link,
                    "Team Stats": m.team_stats,
                    "Extra Stats": m.team_stats_extra,
                }
                for m in self.matches
            ]
        ).to_csv(filename, index=False)
        logger.info(f"Saved {len(self.matches)} matches to {filename}")


if __name__ == "__main__":
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        scraper = SerieAScraper(driver, 2024)
        scraper.scrape_season(max_matches=30)
        scraper.save_to_csv("serie_a_results.csv")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
    finally:
        driver_manager.close()

# TODO: modify waiting logic to be simpler: wait an amount of time between each match request. amount of time should be configurable by parameter in config.py
