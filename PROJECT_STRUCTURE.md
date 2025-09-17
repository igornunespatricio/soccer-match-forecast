# Project Structure: soccer-match-forecast

```
.
├── data
│   └── matches.db
├── ignore
│   ├── model_architecture.png
│   ├── nn_transformer.py
│   ├── system_dependencies_notes.txt
│   └── test.py
├── logs
│   ├── database.log
│   └── ml.log
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
│   ├── generate_markdown_tree.sh
│   ├── getStructure.ps1
│   └── install_chrome.sh
├── src
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
├── PROJECT_STRUCTURE.md
├── README.md
├── main.py
├── poetry.lock
└── pyproject.toml

13 directories, 45 files
```

***
*Generated on: Tue Sep 16 23:30:52 -03 2025*
*Using: `tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea' --dirsfirst | awk filtering`*
*Note: data/processed_tensors directory excluded (contains many UUID folders with tensor files)*
