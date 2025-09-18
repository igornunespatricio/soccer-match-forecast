from src.data.database import DatabaseManager
from src.ml.predict import MatchPredictor
from src.ml.preprocess import Preprocessor
from src.ml.train import MLTrainer
from src.scraper.scraper import SerieAScraper

from src.config import URLS
from src.scraper.webdriver import ChromeDriverWrapper
from src.transform import DataTransformer


def main(
    scrape_basic_match_data: bool = True,
    scrape_match_reports: bool = True,
    transform_data: bool = True,
    preprocess_for_ml: bool = True,
    train_model: bool = True,
    predict_all_matches: bool = True,
):
    # Initialize database
    db = DatabaseManager()
    db.initialize_db()

    # Initialize driver
    if scrape_basic_match_data or scrape_match_reports:
        driver_manager = ChromeDriverWrapper(headless=True)
        driver = driver_manager.get_driver()

        scraper = SerieAScraper(driver)

        # Scrape basic match data
        if scrape_basic_match_data:
            for url in URLS:
                scraper.scrape_basic_match_data(url=url)

        # Scrape match reports
        if scrape_match_reports:
            scraper.scrape_match_reports()

        driver_manager.close()

    if transform_data:
        transformer = DataTransformer()
        transformer.transform()

    if preprocess_for_ml:
        preprocessor = Preprocessor()
        preprocessor.preprocess()

    if train_model:
        trainer = MLTrainer()
        trainer.training_pipeline()

    if predict_all_matches:
        predictor = MatchPredictor()
        predictor.predict_all_matches()


if __name__ == "__main__":
    main(
        scrape_basic_match_data=False,
        scrape_match_reports=False,
        transform_data=False,
        preprocess_for_ml=False,
        train_model=True,
        predict_all_matches=True,
    )
