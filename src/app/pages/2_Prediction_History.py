import streamlit as st

st.title("📅 Predictions History")

from src.config import PREDICT_METADATA_TABLE
from src.data.database import DatabaseManager

db = DatabaseManager()
df = db.get_dataframe(
    f"SELECT season_link, date, home, away, home_win_pred_prob, draw_pred_prob, away_win_pred_prob FROM {PREDICT_METADATA_TABLE} WHERE type='training' ORDER BY date DESC"
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

# reorder columns
df = df[
    [
        "league",
        "date",
        "home",
        "away",
        "Home Win",
        "Draw",
        "Away Win",
    ]
]
st.write(df)
