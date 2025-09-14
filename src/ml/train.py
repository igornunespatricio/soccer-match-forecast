import tensorflow as tf
from src.logger import get_logger
from src.config import ML_TRAINER_LOGGER_PATH, PROCESSED_TENSORS_PATH

logger = get_logger("MLTrainer", ML_TRAINER_LOGGER_PATH)


class MLTrainer:
    def __init__(self):
        self.home_tensor = None
        self.away_tensor = None
        self.target_tensor = None

    def load_data(self):
        """Load tensors from processed_tensors directory"""
        try:
            home_serialized = tf.io.read_file(
                str(PROCESSED_TENSORS_PATH / "home_tensor.ten")
            )
            away_serialized = tf.io.read_file(
                str(PROCESSED_TENSORS_PATH / "away_tensor.ten")
            )
            target_serialized = tf.io.read_file(
                str(PROCESSED_TENSORS_PATH / "target_tensor.ten")
            )
            self.home_tensor = tf.io.parse_tensor(home_serialized, out_type=tf.float32)
            self.away_tensor = tf.io.parse_tensor(away_serialized, out_type=tf.float32)
            self.target_tensor = tf.io.parse_tensor(
                target_serialized, out_type=tf.int32
            )

            logger.info(
                f"Tensors loaded successfully:\nhome: {self.home_tensor.shape}\naway:{self.away_tensor.shape}\ntarget {self.target_tensor.shape}"
            )
        except Exception as e:
            logger.error(f"Error loading tensors: {e}")

    def train_val_test_split(self):
        pass

    def train_model(self):
        pass

    def evaluate_model(self):
        pass

    def save_model(self):
        pass

    def save_metrics(self):
        pass

    def training_pipeline(self):
        self.load_data()
        self.train_val_test_split()
        self.train_model()
        self.evaluate_model()
        self.save_model()
        self.save_metrics()


if __name__ == "__main__":
    trainer = MLTrainer()
    trainer.training_pipeline()
