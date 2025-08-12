from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from typing import List
import pandas as pd
import time

from config import URLS


class Match:
    def __init__(self, date, home, score, away, attendance, report_link, team_stats):
        self.date = date
        self.home = home
        self.score = score
        self.away = away
        self.attendance = attendance
        self.report_link = report_link
        self.team_stats = team_stats


class SerieAScraper:
    def __init__(self, url: str, report_prefix: str = "https://fbref.com"):
        self.url = url
        self.report_prefix = report_prefix
        self.matches: List[Match] = []

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
                    score_cell = row.select_one("td[data-stat='score']")
                    if not score_cell or not score_cell.text.strip():
                        continue  # Skip if score is missing or empty

                    score = score_cell.text.strip()

                    date = row.select_one("td[data-stat='date']").text.strip()
                    home = row.select_one("td[data-stat='home_team']").text.strip()
                    away = row.select_one("td[data-stat='away_team']").text.strip()
                    attendance = row.select_one(
                        "td[data-stat='attendance']"
                    ).text.strip()
                    report_el = row.select_one("td[data-stat='match_report'] a")
                    report_link = (
                        f"{self.report_prefix}{report_el['href']}"
                        if report_el
                        else "N/A"
                    )
                    driver.get(report_link)
                    time.sleep(2)  # Adjust if needed

                    report_soup = BeautifulSoup(driver.page_source, "html.parser")
                    team_stats_div = report_soup.find("div", id="team_stats")

                    team_stats = (
                        team_stats_div.get_text(separator=" | ", strip=True)
                        if team_stats_div
                        else "N/A"
                    )

                    self.matches.append(
                        Match(
                            date, home, score, away, attendance, report_link, team_stats
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
