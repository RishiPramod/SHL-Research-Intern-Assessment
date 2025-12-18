# Submission Summary

## 3 URLs Required

### 1. API Endpoint
**URL**: `https://[YOUR-RAILWAY-APP].railway.app/recommend`

**Method**: POST

**Request Format**:
```json
{
  "query": "Software Engineer role requiring strong problem solving and programming skills"
}
```

**Response Format**:
```json
{
  "recommended_assessments": [
    {
      "url": "https://www.shl.com/...",
      "name": "Assessment Name",
      "adaptive_support": "Yes",
      "description": "Assessment description",
      "duration": 30,
      "remote_support": "Yes",
      "test_type": ["Ability & Aptitude", "Knowledge & Skills"]
    }
  ]
}
```

**Health Check**: `GET https://[YOUR-RAILWAY-APP].railway.app/health`

**Note**: Replace `[YOUR-RAILWAY-APP]` with your actual Railway deployment URL.

---

### 2. GitHub Repository URL
**URL**: `https://github.com/AnshumohanAcharya/SHL-assessment`

This repository contains:
- Complete source code (API, recommendation engine, models)
- All experiments and evaluation code
- Streamlit application for testing
- Data processing scripts
- Requirements and configuration files

---

### 3. Web Application Frontend URL
**URL**: `https://[YOUR-RAILWAY-APP].railway.app/`

The FastAPI application serves a web UI at the root endpoint that provides:
- Interactive job description input
- Real-time assessment recommendations
- Detailed assessment information display
- User-friendly interface for testing

**Note**: Same base URL as the API endpoint - the web frontend is served by the same FastAPI application.

---

## 2-Page Approach Document

See `APPROACH_DOCUMENT.md` in the repository for the complete 2-page document outlining:
- Problem approach and solution architecture
- Initial implementation and baseline performance
- Optimization efforts and performance improvements (85-90% latency reduction)
- Final performance metrics
- Technical decisions and future opportunities

---

## Predictions CSV File

The `predictions.csv` file contains predictions for the test set in the required format:
- **Format**: Two columns - `Query` and `Assessment_url`
- **Content**: Up to 10 recommendations per query
- **Generated using**: The recommendation engine with balanced selection across test types

---

## Key Features

1. **Semantic Search**: Uses sentence transformers (all-MiniLM-L6-v2) for intelligent matching
2. **Pre-computed Embeddings**: 85-90% latency reduction (50-150ms per query)
3. **Balanced Recommendations**: Ensures diversity across test type categories
4. **URL Support**: Automatically extracts text from job description URLs
5. **Robust Filtering**: Multi-criteria filtering with intelligent fallbacks

---

## Testing

After deployment, test the API:
1. Visit the web frontend URL to use the interactive UI
2. Or use curl/Python to test the API endpoint directly
3. Check health endpoint to verify deployment

**Example Test**:
```bash
curl -X POST "https://[YOUR-RAILWAY-APP].railway.app/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Java developer with strong problem-solving skills"}'
```
