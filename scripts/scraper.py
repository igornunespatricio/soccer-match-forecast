from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from scripts.config import RAW_DATA_PATH


class SerieAScoreScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.matches = []

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

    def fetch_page(self):
        self.driver.get(self.url)
        time.sleep(3)

    def extract_scores(self):
        rows = self.driver.find_elements(
            By.XPATH, "//table[contains(@class,'stats_table')]//tbody/tr"
        )
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 9:
                    score = cells[6].text.strip()
                    if score:  # Only include rows with a score
                        match = {
                            "Week": cells[0].text,
                            "Date": cells[2].text,
                            "Time": cells[3].text,
                            "Home Team": cells[4].text,
                            "Home xG": cells[5].text,
                            "Score": score,
                            "Away xG": cells[7].text,
                            "Away Team": cells[8].text,
                            "Venue": cells[10].text if len(cells) > 10 else "",
                        }
                        self.matches.append(match)
            except Exception as e:
                print(f"Error parsing row: {e}")

    def save_to_csv(self, filename="serie_a_scores.csv"):
        RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
        output_path = RAW_DATA_PATH / filename
        df = pd.DataFrame(self.matches)
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} completed matches to {output_path}")

    def run(self):
        self.setup_driver()
        self.fetch_page()
        self.extract_scores()
        self.save_to_csv()
        self.driver.quit()


if __name__ == "__main__":
    scraper = SerieAScoreScraper(
        "https://fbref.com/en/comps/24/schedule/Serie-A-Scores-and-Fixtures"
    )
    scraper.run()
