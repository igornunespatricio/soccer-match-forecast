# Project Structure: soccer-match-forecast

```
.
├── data
│   └── matches.db
├── logs
│   ├── scraper.log
│   └── transformer.log
├── notebooks
│   ├── eda.ipynb
│   └── eda_nn.ipynb
├── scripts
│   ├── generate_markdown_tree.sh
│   ├── getStructure.ps1
│   └── install_chrome.sh
├── src
│   ├── data
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── schemas.py
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
├── notes.txt
├── poetry.lock
├── pyproject.toml
└── test.py

9 directories, 26 files
```

***
*Generated on: Thu Sep 11 17:29:02 -03 2025*
*Using: `tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea' --dirsfirst`*
