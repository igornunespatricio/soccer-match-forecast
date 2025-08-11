import csv
import os
import time
from dataclasses import dataclass
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class Match:
    date: str
    home_team: str
    score: str
    away_team: str
    attendance: str
    report_link: str


class SerieAScraper:
    def __init__(self, url: str):
        self.url = url
        self.driver = self._init_driver()
        self.matches: List[Match] = []

    def _init_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

    def scrape(self) -> List[Match]:
        self.driver.get(self.url)
        time.sleep(3)

        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            try:
                score = row.find_element(
                    By.CSS_SELECTOR, "td[data-stat='score']"
                ).text.strip()
                if "–" not in score:
                    continue

                date = row.find_element(
                    By.CSS_SELECTOR, "td[data-stat='date']"
                ).text.strip()
                home = row.find_element(
                    By.CSS_SELECTOR, "td[data-stat='home_team']"
                ).text.strip()
                away = row.find_element(
                    By.CSS_SELECTOR, "td[data-stat='away_team']"
                ).text.strip()
                attendance = row.find_element(
                    By.CSS_SELECTOR, "td[data-stat='attendance']"
                ).text.strip()
                report_el = row.find_element(
                    By.CSS_SELECTOR, "td[data-stat='match_report'] a"
                )
                report_link = report_el.get_attribute("href") if report_el else "N/A"

                self.matches.append(
                    Match(date, home, score, away, attendance, report_link)
                )
            except Exception:
                continue

        self.driver.quit()
        return self.matches

    def save_to_csv(self, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "Date",
                    "Home Team",
                    "Score",
                    "Away Team",
                    "Attendance",
                    "Match Report Link",
                ]
            )
            for match in self.matches:
                writer.writerow(
                    [
                        match.date,
                        match.home_team,
                        match.score,
                        match.away_team,
                        match.attendance,
                        match.report_link,
                    ]
                )
        print(f"✅ Saved {len(self.matches)} matches to {output_path}")
