#!/bin/bash
# Simple script to output just the tree structure
tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea|processed_tensors' --dirsfirst