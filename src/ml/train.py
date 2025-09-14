from src.logger import get_logger
from src.config import ML_TRAINER_LOGGER_PATH

logger = get_logger("MLTrainer", ML_TRAINER_LOGGER_PATH)


class MLTrainer:
    def __init__(self):
        pass

    def load_data(self):
        pass

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
