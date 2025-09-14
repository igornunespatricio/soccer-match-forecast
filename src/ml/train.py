import tensorflow as tf
from src.logger import get_logger
from src.config import (
    ML_TRAINER_LOGGER_PATH,
    PROCESSED_TENSORS_PATH,
    MODEL_ARCHITECTURE_PATH,
)
from src.ml.models import HybridTransformerModel

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

            logger.info(
                f"Data split successfully:\n Train shape: {self.home_tensor_train.shape}\n Test shape: {self.home_tensor_test.shape}"
            )
        except Exception as e:
            logger.error(f"Error splitting data: {e}")

    def train_model(self):
        """Train model"""
        # Create model
        model = HybridTransformerModel(
            sequence_length=self.home_tensor.shape[1],
            num_features=self.home_tensor.shape[2],
            num_classes=len(tf.unique(self.target_tensor).y),
        )

        # Save model architecture image (this should be in MLTrainer)
        model_architecture_path = MODEL_ARCHITECTURE_PATH / "model_architecture.png"
        self._save_model_architecture_image(
            model.build_model(), model_architecture_path
        )
        logger.info(f"Model architecture saved to {model_architecture_path}")
        # Compile model
        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("Model compiled successfully")

    def _save_model_architecture_image(
        self, model, filepath: str = MODEL_ARCHITECTURE_PATH / "model_architecture.png"
    ):
        """Save model architecture as an image"""
        tf.keras.utils.plot_model(
            model,
            to_file=filepath,
            show_shapes=True,
            show_dtype=True,
            show_layer_names=True,
            rankdir="TB",
            expand_nested=True,
            dpi=200,
            show_layer_activations=True,
            show_trainable=True,
        )

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
