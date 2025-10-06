import pandas as pd
import streamlit as st
from src.config import PREDICT_METADATA_TABLE
from src.data.database import DatabaseManager

st.title("📅 Predictions History")

db = DatabaseManager()
df = db.get_dataframe(
    f"SELECT season_link, date, home, away, winner, home_win_pred_prob, draw_pred_prob, away_win_pred_prob FROM {PREDICT_METADATA_TABLE} WHERE type='training' ORDER BY date DESC"
)
df["league"] = df["season_link"].str.extract(r"(\w+-\w+)(?=-Scores)")

df.drop("season_link", axis=1, inplace=True)

# rename columns
df.rename(
    columns={
        "home_win_pred_prob": "Home Win",
        "draw_pred_prob": "Draw",
        "away_win_pred_prob": "Away Win",
    },
    inplace=True,
)

# convert probabilities to percentage
for col in ["Home Win", "Draw", "Away Win"]:
    df[col] = df[col].apply(lambda x: f"{int(x * 100)} %" if pd.notna(x) else "N/A %")

# mapping winner to strings
df["winner"] = df["winner"].map({"0": "Home", "1": "Away", "2": "Draw"})

# reorder columns
df = df[
    [
        "league",
        "date",
        "home",
        "away",
        "winner",
        "Home Win",
        "Draw",
        "Away Win",
    ]
]
st.write(df)
