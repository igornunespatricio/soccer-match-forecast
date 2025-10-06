import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import PREDICT_METADATA_TABLE
from src.data.database import DatabaseManager

st.title("📊 Model Metrics")

db = DatabaseManager()
df = db.get_dataframe(
    f"""SELECT season_link, date, home, away, winner, score,
                home_win_pred_prob, draw_pred_prob, away_win_pred_prob 
         FROM {PREDICT_METADATA_TABLE} 
         WHERE type='training' AND winner IS NOT NULL 
         ORDER BY date DESC"""
)

if not df.empty:
    # Extract league name
    df["league"] = df["season_link"].str.extract(r"(\w+-\w+)(?=-Scores)")
    df.drop("season_link", axis=1, inplace=True)

    # Map actual winner to readable format
    df["winner"] = df["winner"].map({"0": "Home", "1": "Away", "2": "Draw"})

    # User selectable threshold
    st.sidebar.subheader("Prediction Settings")
    threshold = st.sidebar.slider(
        "Minimum Probability Threshold (%)",
        min_value=0,
        max_value=100,
        value=60,
        step=5,
        help="Only make predictions when the highest probability exceeds this threshold",
    )
    threshold_decimal = threshold / 100

    # Calculate predicted winner with threshold
    def get_predicted_winner_with_threshold(row):
        # Check for NaN values in probabilities
        if (
            pd.isna(row["home_win_pred_prob"])
            or pd.isna(row["draw_pred_prob"])
            or pd.isna(row["away_win_pred_prob"])
        ):
            return "No Prediction"

        max_prob = max(
            row["home_win_pred_prob"], row["draw_pred_prob"], row["away_win_pred_prob"]
        )

        # Only predict if max probability exceeds threshold
        if max_prob >= threshold_decimal:
            if row["home_win_pred_prob"] == max_prob:
                return "Home"
            elif row["draw_pred_prob"] == max_prob:
                return "Draw"
            else:
                return "Away"
        else:
            return "No Prediction"  # Below threshold

    df["predicted_winner"] = df.apply(get_predicted_winner_with_threshold, axis=1)
    df["correct"] = (df["winner"] == df["predicted_winner"]) & (
        df["predicted_winner"] != "No Prediction"
    )

    # Calculate metrics
    total_matches = len(df)
    confident_predictions = len(df[df["predicted_winner"] != "No Prediction"])
    correct_predictions = df["correct"].sum()

    # Accuracy only for confident predictions
    accuracy = (
        (correct_predictions / confident_predictions * 100)
        if confident_predictions > 0
        else 0
    )

    # Coverage (percentage of matches where we made predictions)
    coverage = (confident_predictions / total_matches * 100) if total_matches > 0 else 0

    # Calculate precision and recall for each class (only for confident predictions)
    def calculate_class_metrics(df, class_name):
        confident_df = df[df["predicted_winner"] != "No Prediction"]

        true_positives = (
            (confident_df["winner"] == class_name)
            & (confident_df["predicted_winner"] == class_name)
        ).sum()
        false_positives = (
            (confident_df["winner"] != class_name)
            & (confident_df["predicted_winner"] == class_name)
        ).sum()
        false_negatives = (
            (df["winner"] == class_name)
            & (confident_df["predicted_winner"] != class_name)
        ).sum()

        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0
        )

        return precision * 100, recall * 100

    home_precision, home_recall = calculate_class_metrics(df, "Home")
    away_precision, away_recall = calculate_class_metrics(df, "Away")
    draw_precision, draw_recall = calculate_class_metrics(df, "Draw")

    # Create confusion matrix (only confident predictions)
    confident_df = df[df["predicted_winner"] != "No Prediction"]
    confusion_data = []
    classes = ["Home", "Away", "Draw"]

    for actual in classes:
        for predicted in classes:
            count = (
                (confident_df["winner"] == actual)
                & (confident_df["predicted_winner"] == predicted)
            ).sum()
            confusion_data.append(
                {"Actual": actual, "Predicted": predicted, "Count": count}
            )

    confusion_df = pd.DataFrame(confusion_data)
    confusion_pivot = confusion_df.pivot(
        index="Actual", columns="Predicted", values="Count"
    ).fillna(0)

    # Create confusion matrix plot
    if not confident_df.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(
            confusion_pivot, annot=True, fmt="d", cmap="Blues", cbar=True, ax=ax
        )
        ax.set_title(f"Confusion Matrix (Threshold: {threshold}%)")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
    else:
        fig = None

    # Display metrics
    st.subheader(f"Metrics with {threshold}% Probability Threshold")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Matches", total_matches)
        st.metric("Confident Predictions", confident_predictions)

    with col2:
        st.metric("Correct Predictions", correct_predictions)
        st.metric("Coverage", f"{coverage:.1f}%")

    with col3:
        st.metric("Accuracy", f"{accuracy:.1f}%")
        st.metric("Home Win Precision", f"{home_precision:.1f}%")

    with col4:
        st.metric("Home Win Recall", f"{home_recall:.1f}%")
        st.metric("Away Win Precision", f"{away_precision:.1f}%")

    st.subheader("Class-wise Metrics")
    metrics_df = pd.DataFrame(
        {
            "Class": ["Home Win", "Away Win", "Draw"],
            "Precision": [
                f"{home_precision:.1f}%",
                f"{away_precision:.1f}%",
                f"{draw_precision:.1f}%",
            ],
            "Recall": [
                f"{home_recall:.1f}%",
                f"{away_recall:.1f}%",
                f"{draw_recall:.1f}%",
            ],
        }
    )
    st.write(metrics_df)

    # Display confusion matrix
    if fig:
        st.subheader(f"Confusion Matrix (Threshold: {threshold}%)")
        st.pyplot(fig)

        # Show raw confusion matrix data
        st.write("Confusion Matrix Data:")
        st.write(confusion_pivot)
    else:
        st.warning("No confident predictions made with the current threshold.")

    # Show matches table
    st.subheader("Match Predictions")

    # Format probabilities for display
    display_df = df.copy()

    # Create new columns with proper names - handle NaN values
    display_df["Home Win %"] = display_df["home_win_pred_prob"].apply(
        lambda x: f"{int(x * 100)} %" if pd.notna(x) else "N/A %"
    )
    display_df["Draw %"] = display_df["draw_pred_prob"].apply(
        lambda x: f"{int(x * 100)} %" if pd.notna(x) else "N/A %"
    )
    display_df["Away Win %"] = display_df["away_win_pred_prob"].apply(
        lambda x: f"{int(x * 100)} %" if pd.notna(x) else "N/A %"
    )

    # Add max probability column - handle NaN values
    display_df["Max Probability"] = display_df[
        ["home_win_pred_prob", "draw_pred_prob", "away_win_pred_prob"]
    ].max(axis=1)
    display_df["Max Probability %"] = display_df["Max Probability"].apply(
        lambda x: f"{int(x * 100)} %" if pd.notna(x) else "N/A %"
    )

    # Final columns for display
    display_df = display_df[
        [
            "league",
            "date",
            "home",
            "away",
            "score",
            "winner",
            "predicted_winner",
            "Home Win %",
            "Draw %",
            "Away Win %",
            "Max Probability %",
            "correct",
        ]
    ]

    # Rename for better display
    display_df.rename(
        columns={
            "predicted_winner": "Predicted",
            "correct": "Correct?",
            "winner": "Actual",
        },
        inplace=True,
    )

    st.write(display_df)

else:
    st.warning("No training data with results available for metrics calculation.")
