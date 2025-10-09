#!/bin/bash

# Script to create complete README.md file with project structure
# Usage: ./create_readme.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

README_FILE="README.md"
PROJECT_NAME=$(basename "$(pwd)")

echo -e "${BLUE}Creating complete README.md for: $PROJECT_NAME${NC}"

# Debug: Test the structure script
echo -e "${BLUE}Testing structure script...${NC}"
PROJECT_STRUCTURE=$(./scripts/get_structure.sh)
echo -e "${BLUE}Structure output length: ${#PROJECT_STRUCTURE}${NC}"

# If empty, try alternative approach
if [ -z "$PROJECT_STRUCTURE" ]; then
    echo -e "${RED}Structure is empty, using alternative method...${NC}"
    PROJECT_STRUCTURE=$(tree -a -I '__pycache__|*.pyc|*.db-*|.git|.venv|.vscode|.idea|processed_tensors' --dirsfirst 2>/dev/null || echo "Tree structure unavailable")
fi

echo -e "${BLUE}Final structure preview:${NC}"
echo "---"
echo "$PROJECT_STRUCTURE" | head -10
echo "---"

# Create the complete README.md file
{
    echo "# ⚽ Soccer Match Forecast"
    echo ""
    echo "A machine learning pipeline that predicts soccer match outcomes using web-scraped data and displays results through an interactive Streamlit dashboard."
    echo ""
    echo "## 🚀 What It Does"
    echo ""
    echo "This project automates the entire process of soccer match prediction:"
    echo ""
    echo "1. **📊 Data Collection** - Scrapes match statistics and reports from soccer websites"
    echo "2. **🔄 Data Transformation** - Processes raw data into machine-readable features"
    echo "3. **🤖 Model Training** - Trains neural network models to predict match outcomes (Home Win/Draw/Away Win)"
    echo "4. **📈 Prediction Engine** - Generates probabilities for upcoming matches"
    echo "5. **🎯 Interactive Dashboard** - Displays predictions and historical performance through a Streamlit web app"
    echo ""
    echo "## 📁 Project Structure"
    echo ""
    echo "\`\`\`"
    echo "$PROJECT_STRUCTURE"
    echo "\`\`\`"
    echo ""
    echo "## 🛠️ Features"
    echo ""
    echo "- **Historical Analysis**: Track model performance over time"
    echo "- **Multi-League Support**: Predictions across different soccer leagues"
    echo "- **Interactive Filters**: Explore data by league, team, and date ranges"
    echo "- **Model Metrics**: Precision, recall, and accuracy reporting with confusion matrices"
    echo ""
    echo "## 🎮 Usage"
    echo ""
    echo "1. **Run the full pipeline**:"
    echo "   python main.py"
    echo ""
    echo "2. **Launch the dashboard**:"
    echo "   streamlit run src/app/Home.py"
    echo ""
    echo "3. **Explore the web app**:"
    echo "   - **Home**: Project overview"
    echo "   - **Upcoming Matches**: Future match predictions"
    echo "   - **Prediction History**: Historical predictions with actual results"
    echo "   - **Model Metrics**: Performance analysis and confusion matrices"
    echo ""
    echo "## 📊 Output"
    echo ""
    echo "The system provides:"
    echo "- Match outcome probabilities (Home Win/Draw/Away Win)"
    echo "- Historical prediction accuracy"
    echo "- Confidence-based predictions (adjustable threshold)"
    echo "- Performance metrics and visualizations"
    echo "- Interactive data exploration"
    echo ""
    echo "## 🔧 Technical Stack"
    echo ""
    echo "- **Backend**: Python, SQLite, Neural Networks"
    echo "- **Web Scraping**: Selenium, BeautifulSoup"
    echo "- **ML Framework**: TensorFlow/Keras"
    echo "- **Dashboard**: Streamlit"
    echo "- **Data Processing**: Pandas, NumPy"
    echo ""
    echo "---"
    echo ""
    echo "***"
    echo "*Generated on: $(date)*"
    echo ""
    echo "*Note: data/processed_tensors directory excluded from project structure(contains many UUID folders with tensor files)*"
    
} > "$README_FILE"

echo -e "${GREEN}Complete README.md generated: $README_FILE${NC}"
echo -e "${BLUE}Total lines written: $(wc -l < "$README_FILE")${NC}"