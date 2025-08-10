import pandas as pd

# FBref Série A fixtures URL
URL = "https://fbref.com/en/comps/24/schedule/Serie-A-Scores-and-Fixtures"


def fetch_match_data():
    # Read all tables from the page
    tables = pd.read_html(URL)

    # Assume the first table contains match data
    df = tables[0]

    # Rename columns for clarity
    df.columns = [
        "Week",
        "Day",
        "Date",
        "Time",
        "Home",
        "xG_Home",
        "Score",
        "xG_Away",
        "Away",
        "Attendance",
        "Venue",
        "Referee",
        "Match_Report",
        "Notes",
    ]

    # Filter out rows without a score (i.e., future matches)
    df = df[df["Score"].str.contains("–")]

    return df


if __name__ == "__main__":
    matches = fetch_match_data()
    print(matches.head())

    # Optional: Save to CSV
    matches.to_csv("data/serie_a_matches.csv", index=False)
