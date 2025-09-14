import numpy as np
import pandas as pd
import tensorflow as tf
from tqdm import tqdm
from src.config import (
    PROCESSED_TENSORS_PATH,
    TRANSFORMED_TABLE,
    ML_PROCESSOR_LOGGER_PATH,
)
from src.data.database import DatabaseManager

from src.logger import get_logger

logger = get_logger(
    "MLPreprocessor",
    ML_PROCESSOR_LOGGER_PATH,
)


class Preprocessor:
    def __init__(self, n: str = 10):
        self.db = DatabaseManager()
        self.n = n  # last n matches
        self.df = None

    def read_data(self):
        """Get transformed data from database and return as pandas DataFrame"""
        try:
            self.df = self.db.get_dataframe(
                f"SELECT * FROM {TRANSFORMED_TABLE} ORDER BY date ASC"
            )
            self.df.sort_values("date", inplace=True, ascending=True)
        except Exception as e:
            logger.error(f"Error reading data from database: {e}")
        return self.df

    def _get_feature_cols(self):
        """Get feature columns from DataFrame"""
        try:
            not_feature_cols = [
                "date",
                "home",
                "away",
                "attendance",
                "report_link",
                "date_added",
                "last_updated",
                "season_link",
            ]
            self.feature_cols = [
                col for col in self.df.columns if col not in not_feature_cols
            ]
            self.home_cols = [item for item in self.feature_cols if "home" in item]
            self.away_cols = [item for item in self.feature_cols if "away" in item]
            self._create_constant_tensors()
        except Exception as e:
            logger.error(f"Error getting feature columns: {e}")
        return self.feature_cols, self.home_cols, self.away_cols

    def _create_constant_tensors(self):
        # Create empty tensors
        try:
            self.home_tensor = tf.constant(
                [], dtype=tf.float32, shape=[0, self.n, len(self.feature_cols)]
            )
            self.away_tensor = tf.constant(
                [], dtype=tf.float32, shape=[0, self.n, len(self.feature_cols)]
            )
            self.target_tensor = tf.constant([], dtype=tf.int32, shape=[0])
        except Exception as e:
            logger.error(f"Error creating empty tensors: {e}")
        return self.home_tensor, self.away_tensor, self.target_tensor

    def _filter_last_n_matches(self, team_name: str, date):
        """Return last n matches for team_name before date"""
        try:
            last_n_mask = (self.df["date"] < date) & (
                (self.df["home"] == team_name) | (self.df["away"] == team_name)
            )
        except Exception as e:
            logger.error(f"Error filtering last n matches: {e}")
        return self.df[last_n_mask].tail(self.n)

    def _get_target_value(self, home_score: int, away_score: int):
        """
        Get target value for match
        0: Home win
        1: Away win
        2: Draw
        """
        try:
            target = (
                0 if home_score > away_score else 1 if away_score > home_score else 2
            )
        except Exception as e:
            logger.error(f"Error getting target value: {e}")
        return target

    def _fill_temp_df(
        self, last_n_matches: pd.DataFrame, team_name: str, temp_df: pd.DataFrame
    ):
        """Fill temp dataframe with last n matches for team_name"""
        try:
            for i, (_, item) in enumerate(last_n_matches.iterrows()):
                if item["home"] == team_name:
                    temp_df.loc[i, self.home_cols] = item[self.home_cols].values
                    temp_df.loc[i, self.away_cols] = item[self.away_cols].values
                elif item["away"] == team_name:
                    temp_df.loc[i, self.home_cols] = item[self.away_cols].values
                    temp_df.loc[i, self.away_cols] = item[self.home_cols].values
        except Exception as e:
            logger.error(f"Error filling temp dataframe: {e}")
        return temp_df

    def _process_tensors(self, home_df, away_df, target):
        """Convert temp dataframes to tensors and add to existing tensors"""
        try:
            # Conver to tensors
            home_temp_tensor = tf.convert_to_tensor(home_df.values, dtype=tf.float32)
            away_temp_tensor = tf.convert_to_tensor(away_df.values, dtype=tf.float32)
            target_temp_tensor = tf.convert_to_tensor([target], dtype=tf.int32)
            # Add batch dimension and concatenate
            home_temp_tensor = tf.expand_dims(home_temp_tensor, axis=0)
            away_temp_tensor = tf.expand_dims(away_temp_tensor, axis=0)
            self.home_tensor = tf.concat([self.home_tensor, home_temp_tensor], axis=0)
            self.away_tensor = tf.concat([self.away_tensor, away_temp_tensor], axis=0)
            self.target_tensor = tf.concat(
                [self.target_tensor, target_temp_tensor], axis=0
            )
        except Exception as e:
            logger.error(f"Error processing tensors: {e}")
        return self.home_tensor, self.away_tensor, self.target_tensor

    def _save_processed_tensors(self, path):
        """Save processed tensors using TensorFlow's recommended approach"""
        try:
            # Create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)

            # Save tensors using tf.io.write_file or convert to numpy and save
            tf.io.write_file(
                str(path / "home_tensor.ten"), tf.io.serialize_tensor(self.home_tensor)
            )
            tf.io.write_file(
                str(path / "away_tensor.ten"), tf.io.serialize_tensor(self.away_tensor)
            )
            tf.io.write_file(
                str(path / "target_tensor.ten"),
                tf.io.serialize_tensor(self.target_tensor),
            )
        except Exception as e:
            logger.error(f"Error saving processed tensors: {e}")

    def preprocess(self):
        """Preprocess data and save processed tensors"""
        self.data = self.read_data()
        self._get_feature_cols()

        logger.info(f"Preprocessing {self.df.shape[0]} matches...")
        for i, row in self.df.iterrows():
            # get useful information from row
            temp_date = row["date"]
            home_team = row["home"]
            away_team = row["away"]
            home_score = row["home_score"]
            away_score = row["away_score"]
            report_link = row["report_link"]

            # filters home and away last n matches
            home_last_n = self._filter_last_n_matches(home_team, temp_date)
            away_last_n = self._filter_last_n_matches(away_team, temp_date)

            # only create row if both home and away last n matches are available
            if home_last_n.shape[0] == self.n and away_last_n.shape[0] == self.n:
                target_value = self._get_target_value(home_score, away_score)

                # create temp dataframes
                home_temp_df = pd.DataFrame(
                    columns=self.feature_cols, index=range(self.n)
                )
                away_temp_df = pd.DataFrame(
                    columns=self.feature_cols, index=range(self.n)
                )

                # fill temp dataframes
                home_temp_df = self._fill_temp_df(home_last_n, home_team, home_temp_df)
                away_temp_df = self._fill_temp_df(away_last_n, away_team, away_temp_df)

                # convert to tensor
                if (
                    not home_temp_df.isnull().values.any()
                    and not away_temp_df.isnull().values.any()
                ):
                    self._process_tensors(home_temp_df, away_temp_df, target_value)
                else:
                    logger.info(
                        f"At least one of {self.n} previous matches used to build tensor for match {report_link} is missing data. Skipping..."
                    )
            if i % 100 == 0:
                logger.info(
                    f"Processed {i}/{self.df.shape[0]} matches. Current tensor shape is {self.home_tensor.shape}"
                )
        self._save_processed_tensors(PROCESSED_TENSORS_PATH)
        return self.home_tensor, self.away_tensor, self.target_tensor


if __name__ == "__main__":
    preprocessor = Preprocessor()
    preprocessor.preprocess()
