# src/ml/train.py
import tensorflow as tf
from tensorflow import keras
import numpy as np
import os
from pathlib import Path
from .models import create_hybrid_model, compile_model
from .preprocess import load_processed_tensors  # Assuming you have this function
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Handles model training and evaluation"""

    def __init__(self, data_dir="../data/processed_tensors"):
        self.data_dir = Path(data_dir)
        self.model = None
        self.history = None

    def load_data(self):
        """Load processed tensors from disk"""
        logger.info("Loading processed tensors...")

        # Load tensors (adjust based on your storage format)
        home_tensor = np.load(self.data_dir / "home_tensor.ten", allow_pickle=True)
        away_tensor = np.load(self.data_dir / "away_tensor.ten", allow_pickle=True)
        target_tensor = np.load(self.data_dir / "target_tensor.ten", allow_pickle=True)

        logger.info(f"Home tensor shape: {home_tensor.shape}")
        logger.info(f"Away tensor shape: {away_tensor.shape}")
        logger.info(f"Target tensor shape: {target_tensor.shape}")

        return home_tensor, away_tensor, target_tensor

    def create_model(self, home_tensor, away_tensor, target_tensor):
        """Create and compile the model"""
        sequence_length = home_tensor.shape[1]
        num_features = home_tensor.shape[2]
        num_classes = len(np.unique(target_tensor))

        logger.info(
            f"Creating model with: sequence_length={sequence_length}, "
            f"num_features={num_features}, num_classes={num_classes}"
        )

        self.model = create_hybrid_model(
            sequence_length=sequence_length,
            num_features=num_features,
            num_classes=num_classes,
            num_heads=4,
            dense_units=[128, 64],
            dropout_rates=[0.3, 0.2],
        )

        self.model = compile_model(self.model, learning_rate=0.001)
        self.model.summary()

        return self.model

    def prepare_datasets(
        self,
        home_tensor,
        away_tensor,
        target_tensor,
        test_size=0.2,
        val_size=0.1,
        random_state=42,
    ):
        """Split data into train, validation, and test sets"""
        from sklearn.model_selection import train_test_split

        # First split: separate test set
        home_train, home_test, away_train, away_test, y_train, y_test = (
            train_test_split(
                home_tensor,
                away_tensor,
                target_tensor,
                test_size=test_size,
                random_state=random_state,
                stratify=target_tensor,
            )
        )

        # Second split: separate validation from train
        home_train, home_val, away_train, away_val, y_train, y_val = train_test_split(
            home_train,
            away_train,
            y_train,
            test_size=val_size / (1 - test_size),
            random_state=random_state,
            stratify=y_train,
        )

        logger.info(
            f"Train shapes: home={home_train.shape}, away={away_train.shape}, target={y_train.shape}"
        )
        logger.info(
            f"Validation shapes: home={home_val.shape}, away={away_val.shape}, target={y_val.shape}"
        )
        logger.info(
            f"Test shapes: home={home_test.shape}, away={away_test.shape}, target={y_test.shape}"
        )

        return (
            (home_train, away_train, y_train),
            (home_val, away_val, y_val),
            (home_test, away_test, y_test),
        )

    def create_tf_datasets(self, train_data, val_data, test_data, batch_size=32):
        """Create TensorFlow datasets for training"""
        (home_train, away_train, y_train) = train_data
        (home_val, away_val, y_val) = val_data
        (home_test, away_test, y_test) = test_data

        # Training dataset with shuffling
        train_dataset = (
            tf.data.Dataset.from_tensor_slices(((home_train, away_train), y_train))
            .shuffle(buffer_size=1000)
            .batch(batch_size)
            .prefetch(tf.data.AUTOTUNE)
        )

        # Validation dataset
        val_dataset = (
            tf.data.Dataset.from_tensor_slices(((home_val, away_val), y_val))
            .batch(batch_size)
            .prefetch(tf.data.AUTOTUNE)
        )

        # Test dataset
        test_dataset = (
            tf.data.Dataset.from_tensor_slices(((home_test, away_test), y_test))
            .batch(batch_size)
            .prefetch(tf.data.AUTOTUNE)
        )

        return train_dataset, val_dataset, test_dataset

    def train(self, train_dataset, val_dataset, epochs=50, callbacks=None):
        """Train the model"""
        if callbacks is None:
            callbacks = self._create_callbacks()

        logger.info("Starting model training...")

        self.history = self.model.fit(
            train_dataset,
            validation_data=val_dataset,
            epochs=epochs,
            callbacks=callbacks,
            verbose=1,
        )

        return self.history

    def _create_callbacks(self):
        """Create training callbacks"""
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=10, restore_best_weights=True, verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
            ),
            keras.callbacks.ModelCheckpoint(
                filepath="../logs/best_model.keras",
                monitor="val_loss",
                save_best_only=True,
                verbose=1,
            ),
            keras.callbacks.TensorBoard(
                log_dir="../logs/tensorboard", histogram_freq=1
            ),
        ]
        return callbacks

    def evaluate(self, test_dataset):
        """Evaluate the model on test data"""
        if self.model is None:
            raise ValueError("Model must be trained first")

        logger.info("Evaluating model on test data...")
        results = self.model.evaluate(test_dataset, verbose=1)

        logger.info(f"Test Loss: {results[0]:.4f}")
        logger.info(f"Test Accuracy: {results[1]:.4f}")

        return results

    def save_model(self, path="../logs/trained_model.keras"):
        """Save the trained model"""
        if self.model is None:
            raise ValueError("No model to save")

        self.model.save(path)
        logger.info(f"Model saved to {path}")

    def run_training_pipeline(self, epochs=50, batch_size=32):
        """Complete training pipeline"""
        # Load data
        home_tensor, away_tensor, target_tensor = self.load_data()

        # Create model
        self.create_model(home_tensor, away_tensor, target_tensor)

        # Prepare datasets
        train_data, val_data, test_data = self.prepare_datasets(
            home_tensor, away_tensor, target_tensor
        )

        # Create TF datasets
        train_dataset, val_dataset, test_dataset = self.create_tf_datasets(
            train_data, val_data, test_data, batch_size
        )

        # Train model
        history = self.train(train_dataset, val_dataset, epochs)

        # Evaluate model
        results = self.evaluate(test_dataset)

        # Save model
        self.save_model()

        return history, results


def main():
    """Main training function"""
    trainer = ModelTrainer()
    history, results = trainer.run_training_pipeline(epochs=50, batch_size=32)

    print("Training completed!")
    print(f"Final Test Accuracy: {results[1]:.4f}")


if __name__ == "__main__":
    main()
