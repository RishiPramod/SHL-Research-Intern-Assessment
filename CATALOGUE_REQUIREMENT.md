# Catalogue Requirement

## Important: Catalogue Size Issue

Your evaluation shows **0.0000 Recall@10** because the catalogue currently only contains **2 sample assessments**.

### Requirement
- **Minimum**: 377 Individual Test Solutions
- **Current**: Only 2 sample assessments in `data/catalogue.csv`

### Why This Matters
1. **Evaluation**: Cannot properly evaluate Mean Recall@K with only 2 assessments
2. **Recommendations**: Cannot return minimum 5 recommendations (requirement: 5-10)
3. **Submission**: The system needs the actual scraped SHL catalogue

### What You Need to Do

1. **Scrape the SHL Website**:
   - Visit: https://www.shl.com/solutions/products/product-catalog/
   - Filter for "Individual Test Solutions" (exclude "Pre-packaged Job Solutions")
   - Scrape at least 377 assessments with:
     - URL
     - Name
     - Description
     - Adaptive support
     - Remote support
     - Duration
     - Test type

2. **Save to Catalogue**:
   - Update `data/catalogue.csv` with the scraped data
   - Ensure format matches the expected columns

3. **Verify**:
   ```bash
   python3 -c "import pandas as pd; df = pd.read_csv('data/catalogue.csv'); print(f'Catalogue has {len(df)} assessments')"
   ```

### Current Status
- ✅ Code is ready and working
- ✅ Evaluation script is implemented
- ❌ Catalogue needs to be populated with real data
- ❌ Cannot generate proper recommendations without full catalogue

### Next Steps
1. Create/run a web scraper to collect SHL assessment data
2. Populate `data/catalogue.csv` with at least 377 assessments
3. Re-run evaluation: `python3 evaluate.py`
4. Generate predictions: `python3 generate_predictions.py`
