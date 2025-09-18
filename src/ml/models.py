# src/ml/models.py
import tensorflow as tf
from tensorflow import keras

# from tensorflow import keras
from tensorflow.keras import layers, Model


@tf.keras.utils.register_keras_serializable(
    package="CustomModels", name="TransformerBlock"
)
class TransformerBlock(layers.Layer):
    """Custom Transformer block with residual connection and layer normalization"""

    def __init__(self, num_heads, key_dim, name="transformer_block", **kwargs):
        super().__init__(name=name, **kwargs)
        self.num_heads = num_heads
        self.key_dim = key_dim
        self.multi_head_attention = layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=key_dim, name=f"{name}_attention"
        )
        self.add = layers.Add(name=f"{name}_add")
        self.layer_norm = layers.LayerNormalization(name=f"{name}_layer_norm")

    def call(self, inputs):
        # Self-attention mechanism
        attn_output = self.multi_head_attention(inputs, inputs)
        # Residual connection
        added = self.add([inputs, attn_output])
        # Layer normalization
        return self.layer_norm(added)

    def get_config(self):
        config = super().get_config()
        config.update({"num_heads": self.num_heads, "key_dim": self.key_dim})
        return config


@tf.keras.utils.register_keras_serializable(
    package="CustomModels", name="TeamProcessor"
)
class TeamProcessor(layers.Layer):
    """Processes either home or away team data through the same architecture"""

    def __init__(self, num_heads, key_dim, name="team_processor", **kwargs):
        super().__init__(name=name, **kwargs)
        self.num_heads = num_heads
        self.key_dim = key_dim
        self.batch_norm = layers.BatchNormalization(name=f"{name}_batch_norm")
        self.transformer_block = TransformerBlock(
            num_heads, key_dim, name=f"{name}_transformer"
        )
        self.global_pool = layers.GlobalAveragePooling1D(name=f"{name}_global_pool")

    def call(self, inputs):
        x = self.batch_norm(inputs)
        x = self.transformer_block(x)
        return self.global_pool(x)

    def get_config(self):
        config = super().get_config()
        config.update({"num_heads": self.num_heads, "key_dim": self.key_dim})
        return config


@tf.keras.utils.register_keras_serializable(
    package="CustomModels", name="HybridTransformerModel"
)
class HybridTransformerModel(keras.Model):
    """Hybrid Transformer model for match prediction"""

    def __init__(
        self,
        sequence_length,
        num_features,
        num_classes=3,
        num_heads=4,
        dense_units=[128, 64],
        dropout_rates=[0.3, 0.2],
        model_name="hybrid_transformer",
        **kwargs,
    ):
        # Remove 'name' from kwargs to avoid conflict with model_name
        kwargs.pop("name", None)
        super().__init__(name=model_name, **kwargs)

        self.sequence_length = sequence_length
        self.num_features = num_features
        self.num_classes = num_classes
        self.num_heads = num_heads
        self.dense_units = dense_units
        self.dropout_rates = dropout_rates
        self.model_name = model_name  # Store for serialization

        # Calculate key dimension (ensure it's divisible by num_heads)
        key_dim = max(num_features // num_heads, 1)

        # Team processors (shared or separate weights - using separate here)
        self.home_processor = TeamProcessor(num_heads, key_dim, name="home_processor")
        self.away_processor = TeamProcessor(num_heads, key_dim, name="away_processor")

        # Combination and dense layers
        self.concat = layers.Concatenate()
        self.dense_layers = []
        self.batch_norms = []
        self.dropout_layers = []

        for i, units in enumerate(dense_units):
            self.dense_layers.append(layers.Dense(units, activation="relu"))
            self.batch_norms.append(layers.BatchNormalization())
            if i < len(dropout_rates):
                self.dropout_layers.append(layers.Dropout(dropout_rates[i]))

        self.output_layer = layers.Dense(num_classes, activation="softmax")

    def call(self, inputs):
        home_input, away_input = inputs

        # Process each team
        home_processed = self.home_processor(home_input)
        away_processed = self.away_processor(away_input)

        # Combine representations
        combined = self.concat([home_processed, away_processed])

        # Process through dense layers
        x = combined
        for i in range(len(self.dense_layers)):
            x = self.dense_layers[i](x)
            x = self.batch_norms[i](x)
            if i < len(self.dropout_layers):
                x = self.dropout_layers[i](x)

        return self.output_layer(x)

    def build_model(self):
        """Build the functional model for summary and compilation"""
        home_input = layers.Input(
            shape=(self.sequence_length, self.num_features), name="home_input"
        )
        away_input = layers.Input(
            shape=(self.sequence_length, self.num_features), name="away_input"
        )

        return keras.Model(
            inputs=[home_input, away_input],
            outputs=self.call([home_input, away_input]),
            name=self.name,
        )

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "sequence_length": self.sequence_length,
                "num_features": self.num_features,
                "num_classes": self.num_classes,
                "num_heads": self.num_heads,
                "dense_units": self.dense_units,
                "dropout_rates": self.dropout_rates,
                "model_name": self.model_name,
            }
        )
        return config

    @classmethod
    def from_config(cls, config):
        # Handle the name parameter properly during deserialization
        model_name = config.pop("model_name", "hybrid_transformer")
        return cls(model_name=model_name, **config)


# Factory function for backward compatibility
def create_hybrid_model(sequence_length, num_features, num_classes=3, **kwargs):
    """
    Factory function to create the hybrid transformer model

    Args:
        sequence_length: Number of historical matches
        num_features: Number of features per match
        num_classes: Number of output classes
        **kwargs: Additional arguments for HybridTransformerModel

    Returns:
        Compiled Keras model
    """
    model_class = HybridTransformerModel(
        sequence_length=sequence_length,
        num_features=num_features,
        num_classes=num_classes,
        **kwargs,
    )
    model = model_class.build_model()
    return model


def compile_model(model, learning_rate=0.001):
    """
    Compile the model with appropriate settings
    """
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


if __name__ == "__main__":
    model = create_hybrid_model(sequence_length=10, num_features=40, num_classes=3)
    model.summary()
