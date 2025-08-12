from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from typing import List
import pandas as pd
import time

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
    def __init__(self, url: str, report_prefix: str = "https://fbref.com"):
        self.url = url
        self.report_prefix = report_prefix
        self.matches: List[Match] = []

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
        options = Options()
        options.add_argument("--headless")
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(self.url)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            rows = soup.select("table tbody tr")
            count = 0

            for row in rows:
                if limit is not None and count >= limit:
                    break

                try:
                    match_info = self.extract_basic_match_info(row)
                    if not match_info:
                        continue

                    driver.get(match_info["report_link"])
                    time.sleep(2)

                    report_soup = BeautifulSoup(driver.page_source, "html.parser")
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
            driver.quit()

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
    scraper = SerieAScraper(URLS[2024])
    matches = scraper.scrape(limit=5)
    scraper.save_to_csv()
