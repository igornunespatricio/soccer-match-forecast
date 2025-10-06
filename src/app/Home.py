# src/app/Home.py
import streamlit as st
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)


def main():
    st.set_page_config(page_title="Soccer Predictions", page_icon="⚽", layout="wide")
    st.title("⚽ Soccer Match Prediction Dashboard")
    st.write("Navigate to different sections using the sidebar!")


if __name__ == "__main__":
    main()
