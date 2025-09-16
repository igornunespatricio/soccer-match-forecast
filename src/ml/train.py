import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import tensorflow as tf
from src.data.database import DatabaseManager
from src.logger import get_logger
from src.config import (
    ML_LOGGER_PATH,
    PREDICT_METADATA_TABLE,
    PROCESSED_TENSORS_PATH,
    MODEL_ARTIFACTS_PATH,
    MODEL_ARTIFACTS_PATH,
)
from src.ml.models import HybridTransformerModel

logger = get_logger("MLTrainer", ML_LOGGER_PATH)


class MLTrainer:
    def __init__(self):
        self.db = DatabaseManager()

    def load_data(self):
        """Load tensors from processed_tensors directory"""
        try:
            match_uuid_df = self.db.get_dataframe(
                f"SELECT match_uuid FROM {PREDICT_METADATA_TABLE} WHERE type = 'training'"
            )
            home_tensors = []
            away_tensors = []
            target_tensors = []
            for match_uuid in match_uuid_df["match_uuid"]:
                path = PROCESSED_TENSORS_PATH / match_uuid
                if path.exists():
                    home_serialized = tf.io.read_file(
                        str(PROCESSED_TENSORS_PATH / match_uuid / "home_tensor.ten")
                    )
                    away_serialized = tf.io.read_file(
                        str(PROCESSED_TENSORS_PATH / match_uuid / "away_tensor.ten")
                    )
                    target_serialized = tf.io.read_file(
                        str(PROCESSED_TENSORS_PATH / match_uuid / "target_tensor.ten")
                    )
                    home_tensor_temp = tf.io.parse_tensor(
                        home_serialized, out_type=tf.float32
                    )
                    away_tensor_temp = tf.io.parse_tensor(
                        away_serialized, out_type=tf.float32
                    )
                    target_tensor_temp = tf.io.parse_tensor(
                        target_serialized, out_type=tf.int32
                    )

                    home_tensors.append(home_tensor_temp)
                    away_tensors.append(away_tensor_temp)
                    target_tensors.append(target_tensor_temp)

            # Concatenate all collected tensors
            if home_tensors:
                self.home_tensor = tf.concat(home_tensors, axis=0)
                self.away_tensor = tf.concat(away_tensors, axis=0)
                self.target_tensor = tf.concat(target_tensors, axis=0)
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

    def train_model(self, epochs: int = 30, batch_size: int = 32):
        """Train model"""
        # Create model
        self.model = HybridTransformerModel(
            sequence_length=self.home_tensor.shape[1],
            num_features=self.home_tensor.shape[2],
            num_classes=len(tf.unique(self.target_tensor).y),
        )

        # Save model architecture image (this should be in MLTrainer)
        architecture_path = MODEL_ARTIFACTS_PATH / "model_architecture.png"
        self._save_model_architecture_image(self.model.build_model(), architecture_path)
        logger.info(f"Model architecture saved to {architecture_path}")
        # Compile model
        self.model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("Model compiled successfully")

        # Train the model
        logger.info("Starting model training...")
        self.history = self.model.fit(
            [self.home_tensor_train, self.away_tensor_train],
            self.target_tensor_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_split=0.2,
            callbacks=self._callbacks(),
            verbose=1,
        )

    def _callbacks(self):
        # Define callbacks
        self.callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=10, restore_best_weights=True, verbose=1
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
            ),
            tf.keras.callbacks.ModelCheckpoint(
                filepath=str(MODEL_ARTIFACTS_PATH / "best_model.keras"),
                monitor="val_accuracy",
                save_best_only=True,
                save_weights_only=False,
                verbose=1,
            ),
        ]
        return self.callbacks

    def _save_model_architecture_image(
        self, model, filepath: str = MODEL_ARTIFACTS_PATH / "model_architecture.png"
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

    def save_model(self):
        """Save the trained model"""
        try:
            # Save the full model (architecture + weights + optimizer state)
            model_path = MODEL_ARTIFACTS_PATH / "final_model.keras"
            self.model.save(model_path)
            logger.info(f"Final model saved to {model_path}")

            # Save model architecture separately as well
            architecture_path = MODEL_ARTIFACTS_PATH / "model_architecture.json"
            model_json = self.model.to_json()
            with open(architecture_path, "w") as json_file:
                json_file.write(model_json)
            logger.info(f"Model architecture saved to {architecture_path}")

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise

    def save_metrics(self):
        """Save training history to artifacts directory"""
        try:
            # Save model summary
            summary_path = MODEL_ARTIFACTS_PATH / "model_summary.txt"
            with open(summary_path, "w") as f:
                self.model.summary(print_fn=lambda x: f.write(x + "\n"))
            logger.info(f"Model summary saved to {summary_path}")

            # Save training history as CSV for easy analysis
            history_csv_path = MODEL_ARTIFACTS_PATH / "training_history.csv"

            history_df = pd.DataFrame(self.history.history)
            history_df.to_csv(history_csv_path, index=False)
            logger.info(f"Training history CSV saved to {history_csv_path}")

            # Create and save charts from training history
            self._save_charts_from_history(history_df)

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            raise

    def _save_charts_from_history(
        self, history_df, chart_dir=MODEL_ARTIFACTS_PATH / "charts"
    ):
        """Create charts from training history using melted data approach"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            # create charts dir
            chart_dir.mkdir(parents=True, exist_ok=True)
            # Set style
            sns.set_style("whitegrid")
            plt.rcParams["figure.figsize"] = [10, 6]
            plt.rcParams["font.size"] = 12

            # Add epoch column
            history_df["epoch"] = range(1, len(history_df) + 1)

            # Melt the dataframe for easier plotting
            melted_df = history_df.melt(
                id_vars=["epoch"], var_name="metric", value_name="value"
            )

            # Separate training and validation metrics
            melted_df["metric_type"] = melted_df["metric"].apply(
                lambda x: "validation" if x.startswith("val_") else "training"
            )
            melted_df["metric_name"] = melted_df["metric"].apply(
                lambda x: x[4:] if x.startswith("val_") else x
            )

            # Group by metric name and create individual charts
            unique_metrics = melted_df["metric_name"].unique()

            for metric_name in unique_metrics:
                self._create_single_metric_chart(melted_df, metric_name, chart_dir)

            # Create comprehensive overview chart
            self._create_comprehensive_chart(melted_df, unique_metrics, chart_dir)

        except Exception as e:
            logger.error(f"Error creating charts: {e}")

    def _create_single_metric_chart(self, melted_df, metric_name, chart_dir):
        """Create a single chart for a specific metric"""
        import matplotlib.pyplot as plt

        # Filter data for this metric
        metric_data = melted_df[melted_df["metric_name"] == metric_name]

        if metric_data.empty:
            return

        plt.figure(figsize=(10, 6))

        # Plot training and validation lines
        for metric_type in ["training", "validation"]:
            type_data = metric_data[metric_data["metric_type"] == metric_type]
            if not type_data.empty:
                plt.plot(
                    type_data["epoch"],
                    type_data["value"],
                    label=f"{metric_type.title()} {metric_name}",
                    linewidth=2.5,
                    alpha=0.8,
                )

        # Customize chart
        title = f"{metric_name.title()} Over Epochs"
        ylabel = metric_name.title()

        plt.title(title, fontweight="bold")
        plt.xlabel("Epoch")
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Save chart
        chart_path = chart_dir / f"{metric_name}_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close()
        logger.info(f"{metric_name.title()} chart saved to {chart_path}")

    def _create_comprehensive_chart(self, melted_df, unique_metrics, chart_dir):
        """Create a comprehensive overview chart with subplots"""
        import matplotlib.pyplot as plt

        # Exclude learning rate from main overview
        plot_metrics = [
            m
            for m in unique_metrics
            if "lr" not in m.lower() and "learning_rate" not in m.lower()
        ]

        if not plot_metrics:
            return

        # Determine grid size
        n_metrics = len(plot_metrics)
        n_cols = min(2, n_metrics)
        n_rows = (n_metrics + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))

        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes
        else:
            axes = axes.flatten()

        # Create subplot for each metric
        for idx, metric_name in enumerate(plot_metrics):
            if idx < len(axes):
                ax = axes[idx]
                metric_data = melted_df[melted_df["metric_name"] == metric_name]

                for metric_type in ["training", "validation"]:
                    type_data = metric_data[metric_data["metric_type"] == metric_type]
                    if not type_data.empty:
                        ax.plot(
                            type_data["epoch"],
                            type_data["value"],
                            label=metric_type.title(),
                            linewidth=2,
                        )

                ax.set_title(metric_name.title(), fontweight="bold")
                ax.set_xlabel("Epoch")
                ax.set_ylabel(metric_name.title())
                ax.legend()
                ax.grid(True, alpha=0.3)

        # Hide empty subplots
        for idx in range(len(plot_metrics), len(axes)):
            axes[idx].set_visible(False)

        plt.tight_layout()

        # Save comprehensive chart
        comprehensive_path = chart_dir / "training_metrics_overview.png"
        plt.savefig(comprehensive_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close()
        logger.info(f"Comprehensive metrics overview saved to {comprehensive_path}")

        # TODO: change the scale for the learning rate chart or remove completely
        # Create separate learning rate chart if available
        lr_metrics = [
            m
            for m in unique_metrics
            if "lr" in m.lower() or "learning_rate" in m.lower()
        ]
        if lr_metrics:
            plt.figure(figsize=(10, 6))
            for metric_name in lr_metrics:
                metric_data = melted_df[melted_df["metric_name"] == metric_name]
                for metric_type in ["training", "validation"]:
                    type_data = metric_data[metric_data["metric_type"] == metric_type]
                    if not type_data.empty:
                        plt.plot(
                            type_data["epoch"],
                            type_data["value"],
                            label=f"{metric_type.title()} {metric_name}",
                            linewidth=2.5,
                        )

            plt.title("Learning Rate Schedule", fontweight="bold")
            plt.xlabel("Epoch")
            plt.ylabel("Learning Rate")
            plt.yscale("log")
            plt.legend()
            plt.grid(True, alpha=0.3)

            lr_path = chart_dir / "learning_rate_chart.png"
            plt.savefig(lr_path, dpi=300, bbox_inches="tight", facecolor="white")
            plt.close()
            logger.info(f"Learning rate chart saved to {lr_path}")

    def training_pipeline(self):
        self.load_data()
        self.train_test_split()
        self.train_model(epochs=30, batch_size=64)
        self.save_model()
        self.save_metrics()


if __name__ == "__main__":
    trainer = MLTrainer()
    trainer.training_pipeline()
