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

    def train_test_split(self, test_size: float = 0.2, val_size: float = 0.2):
        """Split data into train and test sets"""
        try:
            total_samples = self.home_tensor.shape[0]
            # Calculate test split indice
            test_split_idx = int(total_samples * (1 - test_size))

            # Split data
            self.home_tensor_train = self.home_tensor[:test_split_idx]
            self.home_tensor_test = self.home_tensor[test_split_idx:]

            self.away_tensor_train = self.away_tensor[:test_split_idx]
            self.away_tensor_test = self.away_tensor[test_split_idx:]

            self.target_tensor_train = self.target_tensor[:test_split_idx]
            self.target_tensor_test = self.target_tensor[test_split_idx:]
            print(self.home_tensor_train.shape, self.home_tensor_test.shape)
            print(self.away_tensor_train.shape, self.away_tensor_test.shape)
            print(self.target_tensor_train.shape, self.target_tensor_test.shape)
            logger.info(
                f"Data split successfully:\n Train shape: {self.home_tensor_train.shape}\n Test shape: {self.home_tensor_test.shape}"
            )
        except Exception as e:
            logger.error(f"Error splitting data: {e}")

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
        self.train_test_split()
        self.train_model()
        self.evaluate_model()
        self.save_model()
        self.save_metrics()


if __name__ == "__main__":
    trainer = MLTrainer()
    trainer.training_pipeline()
