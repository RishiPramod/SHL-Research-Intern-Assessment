# SHL Catalogue Scraping Guide

## Current Status
- ✅ Basic scraper created (`scraper_advanced.py`)
- ⚠️  Only 24 assessments found (need 377+)
- ⚠️  Website may require JavaScript/Selenium

## The Challenge

The SHL website likely:
1. **Loads content via JavaScript** - Need Selenium
2. **Has pagination/infinite scroll** - Need to handle multiple pages
3. **Requires filtering** - Need to filter for "Individual Test Solutions" only
4. **May have anti-scraping measures** - Need proper headers and delays

## Solutions

### Option 1: Use Selenium (Recommended for JavaScript sites)

```bash
# Install Selenium
pip install selenium webdriver-manager

# Run Selenium scraper
python3 scraper_selenium.py
```

**Pros:**
- Handles JavaScript-rendered content
- Can interact with filters and buttons
- Can handle infinite scroll

**Cons:**
- Slower
- Requires Chrome browser
- More complex setup

### Option 2: Manual Data Collection

If scraping is difficult, you can:

1. **Visit the website manually**: https://www.shl.com/solutions/products/product-catalog/
2. **Filter for "Individual Test Solutions"**
3. **Export data** using browser extensions or manual copy
4. **Format as CSV** with columns: url, name, description, adaptive_support, remote_support, duration, test_type

### Option 3: Check for API Endpoint

The website might have an API that provides JSON data:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Visit the catalogue page
4. Look for API calls (XHR/Fetch requests)
5. If found, use those endpoints directly

### Option 4: Use Provided Dataset

Check if the dataset link provided in the assignment contains the catalogue data.

## Required Data Format

Your `data/catalogue.csv` should have these columns:

```csv
url,name,description,adaptive_support,remote_support,duration,test_type
https://www.shl.com/...,Assessment Name,Description text,Yes/No,Yes/No,30,Ability & Aptitude|Knowledge & Skills
```

**Important:**
- At least 377 rows (Individual Test Solutions only)
- Exclude "Pre-packaged Job Solutions"
- `test_type` can be pipe-separated (e.g., "Ability & Aptitude|Knowledge & Skills")

## Next Steps

1. **Try Selenium scraper** (if JavaScript is needed):
   ```bash
   pip install selenium webdriver-manager
   python3 scraper_selenium.py
   ```

2. **Or manually collect data** and format as CSV

3. **Verify catalogue**:
   ```bash
   python3 -c "import pandas as pd; df = pd.read_csv('data/catalogue.csv'); print(f'Found {len(df)} assessments')"
   ```

4. **Once you have 377+ assessments**, run:
   ```bash
   python3 evaluate.py  # Test on train data
   python3 generate_predictions.py  # Generate predictions
   ```

## Troubleshooting

**Only getting 24 assessments?**
- Website may load content dynamically
- Try Selenium scraper
- Check for pagination/filters
- Look for API endpoints in browser DevTools

**Getting blocked?**
- Add delays between requests
- Use proper User-Agent headers
- Consider using proxies (if needed)

**Can't find Individual Test Solutions filter?**
- Check website structure manually
- May need to filter after scraping
- Look for category indicators in URLs or page content
