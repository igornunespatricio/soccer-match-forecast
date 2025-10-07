# ⚽ Soccer Match Forecast

A machine learning pipeline that predicts soccer match outcomes using web-scraped data and displays results through an interactive Streamlit dashboard.

## 🚀 What It Does

This project automates the entire process of soccer match prediction:

1. **📊 Data Collection** - Scrapes match statistics and reports from soccer websites
2. **🔄 Data Transformation** - Processes raw data into machine-readable features
3. **🤖 Model Training** - Trains neural network models to predict match outcomes (Home Win/Draw/Away Win)
4. **📈 Prediction Engine** - Generates probabilities for upcoming matches
5. **🎯 Interactive Dashboard** - Displays predictions and historical performance through a Streamlit web app

## 📁 Project Structure

## 🛠️ Features

- **Historical Analysis**: Track model performance over time
- **Multi-League Support**: Predictions across different soccer leagues
- **Interactive Filters**: Explore data by league, team, and date ranges
- **Model Metrics**: Precision, recall, and accuracy reporting with confusion matrices

## 🎮 Usage

1. **Run the full pipeline**:
```bash
   python main.py
```

2. **Launch the dashboard**:
```bash
   streamlit run src/app/Home.py
```

3. **Explore the web app**:
   - **Home**: Project overview
   - **Upcoming Matches**: Future match predictions
   - **Prediction History**: Historical predictions with actual results
   - **Model Metrics**: Performance analysis and confusion matrices

## 📊 Output

The system provides:
- Match outcome probabilities (Home Win/Draw/Away Win)
- Historical prediction accuracy
- Confidence-based predictions (adjustable threshold)
- Performance metrics and visualizations
- Interactive data exploration

## 🔧 Technical Stack

- **Backend**: Python, SQLite, Neural Networks
- **Web Scraping**: Selenium, BeautifulSoup
- **ML Framework**: TensorFlow/Keras
- **Dashboard**: Streamlit
- **Data Processing**: Pandas, NumPy

---

