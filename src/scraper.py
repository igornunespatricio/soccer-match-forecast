from bs4 import BeautifulSoup
from typing import List
import pandas as pd
from webdriver_manager import (
    WebDriverManager,
)  # assuming you saved it in a separate module

from config import URLS


class Match:
    def __init__(
        self,
        date,
        home,
        score,
        away,
        attendance,
        report_link,
        team_stats,
        team_stats_extra,
    ):
        self.date = date
        self.home = home
        self.score = score
        self.away = away
        self.attendance = attendance
        self.report_link = report_link
        self.team_stats = team_stats
        self.team_stats_extra = team_stats_extra


class SerieAScraper:
    def __init__(
        self,
        year: int,
        driver_manager: WebDriverManager,
        report_prefix: str = "https://fbref.com",
    ):
        self.year = year
        self.url = self._build_url()
        self.driver_manager = driver_manager
        self.report_prefix = report_prefix
        self.matches: List[Match] = []

    def _build_url(self) -> str:
        return f"https://fbref.com/en/comps/24/{self.year}/schedule/{self.year}-Serie-A-Scores-and-Fixtures"

    def extract_team_stats(self, soup: BeautifulSoup) -> dict:
        team_stats_div = soup.find("div", id="team_stats")
        if not team_stats_div:
            return {}

        stats = {}
        rows = team_stats_div.find_all("tr")

        current_label = None
        for row in rows:
            th = row.find("th")
            if th and th.has_attr("colspan") and th["colspan"] == "2":
                current_label = th.get_text(strip=True)
            else:
                tds = row.find_all("td")
                if len(tds) == 2 and current_label:
                    home_value = tds[0].get_text(strip=True)
                    away_value = tds[1].get_text(strip=True)
                    stats[current_label] = {"home": home_value, "away": away_value}
                    current_label = None  # Reset after using

        return stats

    def extract_team_stats_extra(self, soup: BeautifulSoup) -> str:
        extra_stats_div = soup.find("div", id="team_stats_extra")
        if not extra_stats_div:
            return "N/A"

        # Find all <div> blocks that do NOT have class="th"
        stat_blocks = extra_stats_div.find_all("div", recursive=False)
        extracted = []

        for block in stat_blocks:
            items = block.find_all("div")
            for item in items:
                if "th" not in item.get("class", []):
                    text = item.get_text(strip=True)
                    if text:
                        extracted.append(text)

        return " | ".join(extracted)

    def extract_basic_match_info(self, row) -> dict | None:
        score_cell = row.select_one("td[data-stat='score']")
        if not score_cell or not score_cell.text.strip():
            return None  # Skip if score is missing or empty

        try:
            score = score_cell.text.strip()
            date = row.select_one("td[data-stat='date']").text.strip()
            home = row.select_one("td[data-stat='home_team']").text.strip()
            away = row.select_one("td[data-stat='away_team']").text.strip()
            attendance = row.select_one("td[data-stat='attendance']").text.strip()
            report_el = row.select_one("td[data-stat='match_report'] a")
            report_link = (
                f"{self.report_prefix}{report_el['href']}" if report_el else "N/A"
            )

            return {
                "date": date,
                "home": home,
                "score": score,
                "away": away,
                "attendance": attendance,
                "report_link": report_link,
            }
        except Exception as e:
            print(f"Error extracting basic match info: {e}")
            return None

    def scrape(self, limit: int = None) -> List[Match]:
        try:
            soup = BeautifulSoup(
                self.driver_manager.get_page_source(self.url), "html.parser"
            )
            rows = soup.select("table tbody tr")
            count = 0

            for row in rows:
                if limit is not None and count >= limit:
                    break

                try:
                    match_info = self.extract_basic_match_info(row)
                    if not match_info:
                        continue

                    report_html = self.driver_manager.get_page_source(
                        match_info["report_link"]
                    )
                    report_soup = BeautifulSoup(report_html, "html.parser")

                    team_stats = self.extract_team_stats(report_soup)
                    team_stats_extra = self.extract_team_stats_extra(report_soup)

                    self.matches.append(
                        Match(
                            match_info["date"],
                            match_info["home"],
                            match_info["score"],
                            match_info["away"],
                            match_info["attendance"],
                            match_info["report_link"],
                            team_stats,
                            team_stats_extra,
                        )
                    )

                    count += 1
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue

        finally:
            self.driver_manager.quit()

        return self.matches

    def save_to_csv(self, filename: str = "serie_a_matches.csv"):
        if not self.matches:
            print("No matches to save.")
            return

        data = [
            {
                "Date": match.date,
                "Home": match.home,
                "Score": match.score,
                "Away": match.away,
                "Attendance": match.attendance,
                "Match Report": match.report_link,
                "Team Stats": match.team_stats,
                "Team Stats Extra": match.team_stats_extra,
            }
            for match in self.matches
        ]

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} matches to {filename}")


if __name__ == "__main__":

    driver_manager = WebDriverManager(headless=True)
    scraper = SerieAScraper(year=2024, driver_manager=driver_manager)
    matches = scraper.scrape(limit=3)
    scraper.save_to_csv()
