# How to Run Evaluation

## Setup (First Time Only)

1. **Create virtual environment** (if not already created):
   ```bash
   python3 -m venv venv
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running Evaluation

1. **Activate virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. **Run evaluation script**:
   ```bash
   python3 evaluate.py
   ```

This will:
- Load the labeled train data from `Gen_AI Dataset.xlsx`
- Generate recommendations for each query
- Calculate Recall@K for each query
- Compute and display Mean Recall@K

## Generating Predictions

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Generate predictions CSV**:
   ```bash
   python3 generate_predictions.py
   ```

This will create `predictions.csv` with predictions for the test set.

## Notes

- Make sure `Gen_AI Dataset.xlsx` is in the project root directory
- The evaluation script expects the Excel file to have columns for queries and assessment URLs
- The virtual environment (`venv/`) is ignored by git (in `.gitignore`)
