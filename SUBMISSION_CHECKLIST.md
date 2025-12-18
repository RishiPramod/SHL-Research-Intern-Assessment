# Submission Checklist

## ✅ Required Items

### 1. Three URLs

#### API Endpoint
- [ ] **URL**: `https://[YOUR-RAILWAY-APP].railway.app/recommend`
- [ ] Tested and working
- [ ] Returns JSON in correct format
- [ ] Health endpoint working: `/health`

#### GitHub Repository
- [x] **URL**: `https://github.com/AnshumohanAcharya/SHL-assessment`
- [x] Code is accessible
- [x] Includes all experiments and evaluation code

#### Web Application Frontend
- [ ] **URL**: `https://[YOUR-RAILWAY-APP].railway.app/`
- [ ] Tested and working
- [ ] Interactive UI functional

**Action Required**: Replace `[YOUR-RAILWAY-APP]` with your actual Railway deployment URL.

---

### 2. Two-Page Approach Document

- [x] **File**: `APPROACH_DOCUMENT.md`
- [x] Documents solution approach
- [x] Details optimization efforts
- [x] Includes initial results and improvements
- [x] Concise and well-structured

---

### 3. Predictions CSV File

- [ ] **File**: `predictions.csv`
- [ ] Format: Two columns - `Query` and `Assessment_url`
- [ ] Contains predictions for test set
- [ ] Up to 10 recommendations per query

**To Generate**:
```bash
python3 generate_predictions.py
```

This will create `predictions.csv` with the required format.

---

## Files Included in Submission

### Core Application
- `api.py` - FastAPI REST API
- `app.py` - Streamlit application
- `recommender/engine.py` - Recommendation engine
- `models/embedding_model.py` - Embedding model
- `data/catalogue.py` - Data loading
- `utils/text_utils.py` - Text processing utilities

### Documentation
- `APPROACH_DOCUMENT.md` - 2-page approach document
- `SUBMISSION_SUMMARY.md` - Submission summary with URLs
- `README.md` - Project overview

### Configuration
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version
- `Procfile` - Deployment configuration
- `Dockerfile` - Docker configuration

### Submission Files
- `predictions.csv` - Test set predictions (to be generated)
- `generate_predictions.py` - Script to generate predictions

---

## Before Submission

1. ✅ Deploy application on Railway
2. ✅ Get your Railway deployment URL
3. ✅ Update URLs in `SUBMISSION_SUMMARY.md`
4. ✅ Generate `predictions.csv` using `generate_predictions.py`
5. ✅ Test all three URLs
6. ✅ Verify GitHub repository is accessible
7. ✅ Review `APPROACH_DOCUMENT.md` (should be ~2 pages)

---

## Testing Your Submission

### Test API Endpoint
```bash
curl -X POST "https://[YOUR-RAILWAY-APP].railway.app/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Java developer with strong problem-solving skills"}'
```

### Test Health Check
```bash
curl https://[YOUR-RAILWAY-APP].railway.app/health
```

### Test Web Frontend
Open in browser: `https://[YOUR-RAILWAY-APP].railway.app/`

---

## Notes

- All deployment documentation has been removed as requested
- Only submission-relevant files remain
- The approach document is concise and focused on optimization efforts
- The predictions CSV will be generated from the test set in `Gen_AI Dataset.xlsx`
