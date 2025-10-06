import pandas as pd
import streamlit as st
from src.config import PREDICT_METADATA_TABLE
from src.data.database import DatabaseManager

# Page configuration
st.set_page_config(page_title="Predictions History", page_icon="📅", layout="wide")
st.title("📅 Predictions History")
st.markdown("Explore historical match predictions and their outcomes.")


# Load data with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    db = DatabaseManager()
    df = db.get_dataframe(
        f"SELECT season_link, date, home, away, winner, home_win_pred_prob, draw_pred_prob, away_win_pred_prob FROM {PREDICT_METADATA_TABLE} WHERE type='training' ORDER BY date DESC"
    )
    return df


# Load data
df = load_data()

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

    # Date range filter
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

    # Result filter
    result_options = ["All", "Home Win", "Away Win", "Draw"]
    selected_result = st.sidebar.selectbox("Filter by Result", result_options)

    # Apply filters
    filtered_df = df.copy()

    if selected_league != "All":
        filtered_df = filtered_df[filtered_df["league"] == selected_league]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["date"] >= pd.Timestamp(start_date))
            & (filtered_df["date"] <= pd.Timestamp(end_date))
        ]

    if selected_team != "All":
        filtered_df = filtered_df[
            (filtered_df["home"] == selected_team)
            | (filtered_df["away"] == selected_team)
        ]

    # Map winner to strings
    filtered_df["winner"] = filtered_df["winner"].map(
        {"0": "Home", "1": "Away", "2": "Draw"}
    )

    if selected_result != "All":
        result_map = {"Home Win": "Home", "Away Win": "Away", "Draw": "Draw"}
        filtered_df = filtered_df[filtered_df["winner"] == result_map[selected_result]]

    # Rename and format columns
    filtered_df = filtered_df.rename(
        columns={
            "home_win_pred_prob": "Home Win",
            "draw_pred_prob": "Draw",
            "away_win_pred_prob": "Away Win",
        }
    )

    # Convert probabilities to percentage
    for col in ["Home Win", "Draw", "Away Win"]:
        filtered_df[col] = filtered_df[col].apply(
            lambda x: f"{int(x * 100)} %" if pd.notna(x) else "N/A %"
        )

    # Reorder columns
    filtered_df = filtered_df[
        ["league", "date", "home", "away", "winner", "Home Win", "Draw", "Away Win"]
    ]

    # Display summary metrics
    st.subheader("📊 Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Matches", len(filtered_df))

    with col2:
        home_wins = len(filtered_df[filtered_df["winner"] == "Home"])
        st.metric("Home Wins", home_wins)

    with col3:
        away_wins = len(filtered_df[filtered_df["winner"] == "Away"])
        st.metric("Away Wins", away_wins)

    with col4:
        draws = len(filtered_df[filtered_df["winner"] == "Draw"])
        st.metric("Draws", draws)

    # Display data
    st.subheader("📋 Match Predictions")

    # Search functionality
    search_term = st.text_input("🔍 Search matches (team names, league)...", "")
    if search_term:
        search_mask = (
            filtered_df["home"].str.contains(search_term, case=False, na=False)
            | filtered_df["away"].str.contains(search_term, case=False, na=False)
            | filtered_df["league"].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]

    # Show/hide columns
    st.sidebar.header("📊 Display Options")
    default_columns = [
        "league",
        "date",
        "home",
        "away",
        "winner",
        "Home Win",
        "Draw",
        "Away Win",
    ]
    selected_columns = st.sidebar.multiselect(
        "Select columns to display", options=default_columns, default=default_columns
    )

    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Date (Newest)", "Date (Oldest)", "Home Team", "Away Team", "League"],
    )

    sort_map = {
        "Date (Newest)": "date",
        "Date (Oldest)": "date",
        "Home Team": "home",
        "Away Team": "away",
        "League": "league",
    }

    if sort_by in sort_map:
        ascending = sort_by == "Date (Oldest)"
        filtered_df = filtered_df.sort_values(by=sort_map[sort_by], ascending=ascending)

    # Display the dataframe with styling
    if not filtered_df.empty:
        st.dataframe(
            filtered_df[selected_columns], use_container_width=True, height=600
        )
    else:
        st.warning("No matches found with the selected filters.")
        st.info("Try adjusting your filter criteria to see more results.")

    # Show raw data option
    with st.expander("📁 View Raw Data"):
        st.write(filtered_df)

else:
    st.warning("No prediction history data available.")
    st.info("This could be because:")
    st.markdown(
        """
    - No training data has been processed yet
    - The database doesn't contain prediction records
    - There was an issue loading the data
    """
    )

# Footer
st.markdown("---")
st.caption("💡 Use the sidebar filters to explore specific matches and leagues.")
