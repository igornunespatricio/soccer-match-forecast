# Project Structure: soccer-match-forecast

```
.
├── data
│   ├── processed_tensors
│   │   ├── away_tensor.ten
│   │   ├── home_tensor.ten
│   │   └── target_tensor.ten
│   └── matches.db
├── ignore
│   ├── nn_transformer.py
│   └── test.py
├── logs
│   ├── database.log
│   ├── ml_preprocessor.log
│   ├── ml_trainer.log
│   └── scraper.log
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

12 directories, 37 files
```

***
*Generated on: Sun Sep 14 00:02:08 -03 2025*
*Using: `tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea' --dirsfirst`*
