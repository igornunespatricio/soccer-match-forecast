import logging
import os
from pathlib import Path
from src.config import SCRAPER_LOGGER_PATH  # Import from config


# TODO: keep log for last 7 days
def get_logger(
    name: str = "scraper", log_file_path: Path = SCRAPER_LOGGER_PATH
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Use the provided log_file_path or fall back to config's SCRAPER_LOGGER_PATH
    if log_file_path is None:
        log_file_path = SCRAPER_LOGGER_PATH

    # Ensure the log directory exists
    os.makedirs(log_file_path.parent, exist_ok=True)

    # File handler
    fh = logging.FileHandler(log_file_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
