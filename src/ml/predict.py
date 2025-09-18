import tensorflow as tf
import numpy as np
from src.config import (
    ML_LOGGER_PATH,
    MODEL_ARTIFACTS_PATH,
    PREDICT_METADATA_TABLE,
    PROCESSED_TENSORS_PATH,
)
from src.data.database import DatabaseManager
from src.ml.models import HybridTransformerModel
from src.logger import get_logger

logger = get_logger("MLPredictor", ML_LOGGER_PATH)


class MatchPredictor:
    def __init__(self, model_path: str = MODEL_ARTIFACTS_PATH / "best_model.keras"):
        self.model_path = model_path
        self.model = self._load_model()
        self.db = DatabaseManager()

    def _load_model(self):
        """Load the trained model"""
        return tf.keras.models.load_model(self.model_path)

    def _load_tensors(self, match_uuid: str):
        """Load tensors from processed_tensors directory"""
        path = PROCESSED_TENSORS_PATH / match_uuid
        if path.exists():
            try:
                home_serialized = tf.io.read_file(str(path / "home_tensor.ten"))
                away_serialized = tf.io.read_file(str(path / "away_tensor.ten"))
                home_tensor = tf.io.parse_tensor(home_serialized, out_type=tf.float32)
                away_tensor = tf.io.parse_tensor(away_serialized, out_type=tf.float32)
                return home_tensor, away_tensor
            except Exception as e:
                logger.error(f"Error loading tensors for {match_uuid}: {e}")
                return None, None
        return None, None

    def _get_all_matches_to_predict(self):
        """Get all matches from predict_metadata_table that need predictions"""
        query = f"""
        SELECT match_uuid, season_link, date, home, away, score, winner, type, report_link
        FROM {PREDICT_METADATA_TABLE}
        WHERE home_win_pred_prob IS NULL 
           OR draw_pred_prob IS NULL 
           OR away_win_pred_prob IS NULL
           OR type='prediction'
        ORDER BY date
        """
        return self.db.get_dataframe(query)

    def _get_single_match_to_predict(
        self, home_team: str, away_team: str, match_date: str
    ):
        """Get a single match from predict_metadata_table"""
        query = f"""
        SELECT match_uuid, season_link, date, home, away, score, winner, type, report_link
        FROM {PREDICT_METADATA_TABLE}
        WHERE date = ? AND home = ? AND away = ?
        """
        return self.db.get_dataframe(query, params=(match_date, home_team, away_team))

    def _extract_probabilities(self, predictions):
        """
        Extract home win, draw, and away win probabilities from model predictions

        Args:
            predictions: Model output tensor

        Returns:
            tuple: (home_win_prob, draw_prob, away_win_prob)
        """
        home_win_prob = predictions[0][0]
        away_win_prob = predictions[0][1]
        draw_prob = predictions[0][2]
        return home_win_prob, draw_prob, away_win_prob

    def _update_prediction_in_db(
        self, match_uuid, home_win_prob, draw_prob, away_win_prob
    ):
        """Update the database with prediction results"""
        update_query = f"""
        UPDATE {PREDICT_METADATA_TABLE}
        SET home_win_pred_prob = ?,
            draw_pred_prob = ?,
            away_win_pred_prob = ?,
            last_updated = CURRENT_TIMESTAMP
        WHERE match_uuid = ?
        """
        self.db.execute_query(
            update_query,
            params=(
                float(home_win_prob),
                float(draw_prob),
                float(away_win_prob),
                match_uuid,
            ),
        )

    def predict_single_match(self, home_team: str, away_team: str, match_date: str):
        """Predict a single match using DataFrame approach"""
        matches_df = self._get_single_match_to_predict(home_team, away_team, match_date)

        if matches_df.empty:
            logger.error(f"Match not found: {home_team} vs {away_team} on {match_date}")
            return None

        match = matches_df.iloc[0]
        match_uuid = match["match_uuid"]
        home_tensor, away_tensor = self._load_tensors(match_uuid)

        if home_tensor is None or away_tensor is None:
            logger.error(f"Tensors not found for match {match_uuid}")
            return None

        logger.info(f"Predicting match {home_team} vs {away_team} on {match_date}")
        predictions = self.model.predict([home_tensor, away_tensor])

        # Extract probabilities using the new method
        home_win_prob, draw_prob, away_win_prob = self._extract_probabilities(
            predictions
        )

        logger.info(
            f"Predictions: Home: {home_win_prob:.3f}, Draw: {draw_prob:.3f}, Away: {away_win_prob:.3f}"
        )

        # Update database
        self._update_prediction_in_db(
            match_uuid, home_win_prob, draw_prob, away_win_prob
        )

        return predictions

    def predict_all_matches(self):
        """Predict all matches in the database that don't have predictions yet"""
        matches_df = self._get_all_matches_to_predict()

        if matches_df.empty:
            logger.info("No matches need predictions")
            return

        total_matches = len(matches_df)
        logger.info(f"Found {total_matches} matches to predict")

        successful_predictions = 0
        failed_predictions = 0

        for i, (_, match) in enumerate(matches_df.iterrows()):
            match_uuid = match["match_uuid"]
            season_link = match["season_link"]
            date = match["date"]
            home = match["home"]
            away = match["away"]
            score = match["score"]
            winner = match["winner"]
            match_type = match["type"]
            report_link = match["report_link"]

            # Log progress every 100 matches
            if (i + 1) % 100 == 0 or (i + 1) == total_matches:
                progress_percent = ((i + 1) / total_matches) * 100
                logger.info(
                    f"Progress: {i + 1} of {total_matches} matches processed ({progress_percent:.1f}%)"
                )
            else:
                # Debug level for individual matches to reduce log noise
                logger.debug(
                    f"Processing: {home} vs {away} on {date} (UUID: {match_uuid})"
                )

            home_tensor, away_tensor = self._load_tensors(match_uuid)

            if home_tensor is None or away_tensor is None:
                logger.warning(f"Skipping {match_uuid}: Tensors not found")
                failed_predictions += 1
                continue

            try:
                # Make prediction
                predictions = self.model.predict([home_tensor, away_tensor], verbose=0)

                # Extract probabilities using the new method
                home_win_prob, draw_prob, away_win_prob = self._extract_probabilities(
                    predictions
                )

                # Update database
                self._update_prediction_in_db(
                    match_uuid, home_win_prob, draw_prob, away_win_prob
                )

                # Debug level for individual predictions to reduce log noise
                logger.debug(
                    f"Predicted {home} vs {away}: H: {home_win_prob:.3f}, D: {draw_prob:.3f}, A: {away_win_prob:.3f}"
                )
                successful_predictions += 1

            except Exception as e:
                logger.error(f"Error predicting match {match_uuid}: {e}")
                failed_predictions += 1

        logger.info(
            f"Prediction completed. Successful: {successful_predictions}, Failed: {failed_predictions}"
        )

    def get_prediction_stats(self):
        """Get statistics about predictions in the database"""
        stats_query = f"""
        SELECT 
            COUNT(*) as total_matches,
            COUNT(CASE WHEN home_win_pred_prob IS NOT NULL THEN 1 END) as predicted_matches,
            COUNT(CASE WHEN home_win_pred_prob IS NULL THEN 1 END) as pending_matches
        FROM {PREDICT_METADATA_TABLE}
        """
        result = self.db.execute_query(stats_query)
        return {
            "total_matches": result[0][0],
            "predicted_matches": result[0][1],
            "pending_matches": result[0][2],
        }


if __name__ == "__main__":
    predictor = MatchPredictor()

    # Option 1: Predict all matches that need predictions
    predictor.predict_all_matches()

    # Option 2: Predict a specific match
    # predictor.predict_single_match("Brentford", "Arsenal", "2025-01-01")

    # Show prediction statistics
    # stats = predictor.get_prediction_stats()
    # logger.info(f"Prediction statistics: {stats}")
