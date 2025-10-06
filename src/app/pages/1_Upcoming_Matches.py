import pandas as pd
import streamlit as st
from src.config import PREDICT_METADATA_TABLE
from src.data.database import DatabaseManager

# Page configuration
st.set_page_config(page_title="Upcoming Matches", page_icon="📅", layout="wide")
st.title("📅 Upcoming Match Predictions")
st.markdown("View predictions for upcoming soccer matches.")


# Load data with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_upcoming_matches():
    db = DatabaseManager()
    df = db.get_dataframe(
        f"SELECT season_link, date, home, away, home_win_pred_prob, draw_pred_prob, away_win_pred_prob FROM {PREDICT_METADATA_TABLE} WHERE type='prediction' ORDER BY date ASC"
    )
    return df


# Load data
df = load_upcoming_matches()

if not df.empty:
    # Data preprocessing
    df["league"] = df["season_link"].str.extract(r"(\w+-\w+)(?=-Scores)")
    df.drop("season_link", axis=1, inplace=True)

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # League filter
    leagues = ["All"] + sorted(df["league"].unique().tolist())
    selected_league = st.sidebar.selectbox("Select League", leagues)

    # Filter teams based on selected league
    if selected_league == "All":
        available_teams_df = df
    else:
        available_teams_df = df[df["league"] == selected_league]

    # Get unique teams from the filtered dataframe
    all_teams = sorted(
        set(
            available_teams_df["home"].unique().tolist()
            + available_teams_df["away"].unique().tolist()
        )
    )
    selected_team = st.sidebar.selectbox("Filter by Team", ["All"] + all_teams)

    # Date filter
    if pd.api.types.is_datetime64_any_dtype(df["date"]):
        min_date = df["date"].min()
        max_date = df["date"].max()
    else:
        df["date"] = pd.to_datetime(df["date"])
        min_date = df["date"].min()
        max_date = df["date"].max()

    date_range = st.sidebar.date_input(
        "Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )

    # Apply filters
    filtered_df = df.copy()

    if selected_league != "All":
        filtered_df = filtered_df[filtered_df["league"] == selected_league]

    if selected_team != "All":
        filtered_df = filtered_df[
            (filtered_df["home"] == selected_team)
            | (filtered_df["away"] == selected_team)
        ]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["date"] >= pd.Timestamp(start_date))
            & (filtered_df["date"] <= pd.Timestamp(end_date))
        ]

    # Rename columns
    filtered_df = filtered_df.rename(
        columns={
            "home_win_pred_prob": "Home Win %",
            "draw_pred_prob": "Draw %",
            "away_win_pred_prob": "Away Win %",
        }
    )

    # Convert probabilities to percentages
    for col in ["Home Win %", "Draw %", "Away Win %"]:
        filtered_df[col] = (filtered_df[col] * 100).round(1).astype(str) + "%"

    # Reorder columns
    filtered_df = filtered_df[
        ["league", "date", "home", "away", "Home Win %", "Draw %", "Away Win %"]
    ]

    # Display summary
    st.subheader("📊 Overview")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Upcoming Matches", len(filtered_df))

    with col2:
        unique_leagues = filtered_df["league"].nunique()
        st.metric("Leagues", unique_leagues)

    with col3:
        if not filtered_df.empty:
            next_match_date = filtered_df["date"].min()
            st.metric("Next Match Date", next_match_date.strftime("%Y-%m-%d"))
        else:
            st.metric("Next Match Date", "N/A")

    # Display matches
    st.subheader("🎯 Match Predictions")

    # Display the dataframe with better formatting
    if not filtered_df.empty:
        # Style the dataframe
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=600,
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Home Win %": st.column_config.TextColumn("Home Win"),
                "Draw %": st.column_config.TextColumn("Draw"),
                "Away Win %": st.column_config.TextColumn("Away Win"),
            },
        )

        # Show match count
        st.caption(f"Showing {len(filtered_df)} upcoming match(es)")

    else:
        st.warning("No upcoming matches found with the selected filters.")
        st.info(
            "Try adjusting your filter criteria or check back later for new predictions."
        )

else:
    st.warning("No upcoming match predictions available.")
    st.info("This could be because:")
    st.markdown(
        """
    - No prediction data has been generated yet
    - All predictions have already been played
    - There was an issue loading the data
    """
    )

# Footer
st.markdown("---")
st.caption("💡 Use the sidebar filters to focus on specific leagues, dates, or teams.")
