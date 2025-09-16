import tensorflow as tf
from src.config import MODEL_ARTIFACTS_PATH


class MatchPredictor:
    def __init__(self, model_path: str = MODEL_ARTIFACTS_PATH / "best_model.keras"):
        self.model_path = model_path

    def _load_model(self):
        self.model = tf.keras.models.load_model(self.model_path)

    def predict(self, home_tensor, away_tensor):
        self.load_model()


if __name__ == "__main__":
    predictor = MatchPredictor()
    predictor.predict()
