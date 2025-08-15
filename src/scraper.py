import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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
        self.matches = []
        self.base_file_path = RAW_DATA_PATH / f"serie_a_{self.year}_results.csv"

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

    def scrape_basic_match_data(self) -> None:
        """Scrape basic match data, merging with existing data while preserving scraped reports"""
        base_url = f"https://fbref.com/en/comps/24/{self.year}/schedule/{self.year}-Serie-A-Scores-and-Fixtures"
        soup = self._get_page(base_url)

        # Scrape fresh basic data
        new_matches = []
        for row in soup.select("table.stats_table tbody tr"):
            if match := self._extract_match_data(row):
                new_matches.append(match)
        new_df = pd.DataFrame(new_matches)

        # Try to load existing data
        existing_df = pd.DataFrame()
        if self.base_file_path.exists():
            try:
                existing_df = pd.read_csv(self.base_file_path)
                # Ensure required columns exist
                for col in ["Team Stats", "Extra Stats"]:
                    if col not in existing_df.columns:
                        existing_df[col] = None
            except (pd.errors.EmptyDataError, Exception) as e:
                logger.warning(f"Could not read existing file: {e}")

        # Merge data using report_link as key
        if not existing_df.empty:
            # Full outer join on report_link
            merged_df = pd.merge(
                new_df,
                existing_df[["report_link", "Team Stats", "Extra Stats"]],
                on="report_link",
                how="outer",
                suffixes=("", "_existing"),
            )

            # For matches with existing stats, keep them; otherwise use new data
            final_df = pd.concat(
                [
                    # Existing matches with stats
                    existing_df[existing_df["Team Stats"].notna()],
                    # New matches or existing matches without stats
                    new_df[
                        ~new_df["report_link"].isin(
                            existing_df[existing_df["Team Stats"].notna()][
                                "report_link"
                            ]
                        )
                    ],
                ]
            ).drop_duplicates("report_link")
        else:
            final_df = new_df

        # Ensure standard columns
        if "Team Stats" not in final_df.columns:
            final_df["Team Stats"] = None
        if "Extra Stats" not in final_df.columns:
            final_df["Extra Stats"] = None

        # Save merged data
        final_df.to_csv(self.base_file_path, index=False)
        logger.info(
            f"Merged and saved {len(final_df)} matches to {self.base_file_path}"
        )

    def scrape_match_reports(self, max_matches=None) -> List[Match]:
        """Scrape match reports incrementally while preserving existing data"""
        try:
            # Load existing data with proper type conversion
            existing_df = pd.read_csv(
                self.base_file_path,
                converters={
                    "Team Stats": lambda x: (
                        eval(x) if pd.notna(x) and x not in ["", "N/A"] else {}
                    ),
                    "Extra Stats": lambda x: x if pd.notna(x) else "N/A",
                },
            )
        except FileNotFoundError:
            logger.error(
                "No saved match data found. Run scrape_basic_match_data() first."
            )
            return []
        except Exception as e:
            logger.error(f"Error reading data file: {e}")
            return []

        # Convert to list of dicts for processing
        all_matches = existing_df.to_dict("records")
        total_matches = len(all_matches)
        processed_count = sum(1 for m in all_matches if m.get("Team Stats"))

        logger.info(
            f"Resuming from {processed_count}/{total_matches} already processed matches"
        )

        for i, match in enumerate(all_matches):
            if max_matches and i >= max_matches:
                break

            # Skip if already processed or missing report link
            if not match.get("report_link") or match.get("Team Stats"):
                continue

            for attempt in range(MAX_RETRIES):
                try:
                    # Scrape match report
                    report_soup = self._get_page(match["report_link"])
                    team_stats, extra_stats = self._extract_stats(report_soup)

                    # Update only this match's data in the DataFrame
                    existing_df.loc[
                        existing_df["report_link"] == match["report_link"],
                        ["Team Stats", "Extra Stats"],
                    ] = [str(team_stats), extra_stats]

                    # Save incrementally after each successful scrape
                    existing_df.to_csv(self.base_file_path, index=False)

                    logger.info(
                        f"({i+1}/{total_matches}) Scraped: {match['home']} vs {match['away']} | "
                        f"Progress: {processed_count + 1}/{total_matches}"
                    )
                    processed_count += 1
                    break

                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        logger.error(
                            f"Failed after {MAX_RETRIES} attempts for match {i+1}: {e}\n"
                            f"Match: {match['home']} vs {match['away']} | {match['report_link']}"
                        )
                        # Save progress even on failure to maintain position
                        existing_df.to_csv(self.base_file_path, index=False)
                    else:
                        wait_time = REQUEST_DELAY * (attempt + 1)
                        logger.warning(
                            f"Attempt {attempt+1} failed for match {i+1}, "
                            f"retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)

        # Convert back to Match objects
        self.matches = [
            Match(
                date=row["date"],
                home=row["home"],
                score=row["score"],
                away=row["away"],
                attendance=row["attendance"],
                report_link=row["report_link"],
                team_stats=(
                    eval(row["Team Stats"]) if pd.notna(row["Team Stats"]) else {}
                ),
                team_stats_extra=row["Extra Stats"],
            )
            for _, row in existing_df.iterrows()
        ]
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
        logger.info(f"Saved {len(self.matches)} complete matches to {filename}")


if __name__ == "__main__":
    driver_manager = ChromeDriverWrapper(headless=True)
    driver = driver_manager.get_driver()

    try:
        year = 2024
        scraper = SerieAScraper(driver, year)

        # Phase 1: Scrape basic match data
        scraper.scrape_basic_match_data()

        # Phase 2: Scrape detailed reports
        scraper.scrape_match_reports()

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
    finally:
        driver_manager.close()
