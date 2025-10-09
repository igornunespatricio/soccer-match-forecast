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

```
.
├── data
│   └── matches.db
├── ignore
│   ├── model_architecture.png
│   ├── nn_transformer.py
│   ├── notes.txt
│   ├── system_dependencies_notes.txt
│   └── test.py
├── logs
│   ├── database.log
│   ├── ml.log
│   ├── scraper.log
│   └── transformer.log
├── model_artifacts
│   ├── charts
│   │   ├── accuracy_chart.png
│   │   ├── learning_rate_chart.png
│   │   ├── loss_chart.png
│   │   └── training_metrics_overview.png
│   ├── best_model.keras
│   ├── final_model.keras
│   ├── model_architecture.json
│   ├── model_architecture.png
│   ├── model_summary.txt
│   └── training_history.csv
├── notebooks
│   ├── eda.ipynb
│   ├── eda_nn.ipynb
│   ├── eda_nn_specialized_model.ipynb
│   └── eda_nn_transformer.ipynb
├── scripts
│   ├── create_readme.sh
│   ├── generate_markdown_tree.sh
│   ├── getStructure.ps1
│   ├── get_structure.sh
│   └── install_chrome.sh
├── src
│   ├── app
│   │   ├── pages
│   │   │   ├── 1_Upcoming_Matches.py
│   │   │   ├── 2_Prediction_History.py
│   │   │   ├── 3_Model_Metrics.py
│   │   │   └── __init__.py
│   │   ├── Home.py
│   │   └── __init__.py
│   ├── data
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── schemas.py
│   ├── ml
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── predict.py
│   │   ├── preprocess.py
│   │   └── train.py
│   ├── scraper
│   │   ├── __init__.py
│   │   ├── scraper.py
│   │   └── webdriver.py
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   └── transform.py
├── tests
├── .gitignore
├── README.md
├── main.py
├── poetry.lock
└── pyproject.toml

15 directories, 55 files
```

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

***
*Generated on: Thu Oct  9 13:13:01 -03 2025*

*Note: data/processed_tensors directory excluded from project structure(contains many UUID folders with tensor files)*
