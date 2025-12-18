# SHL Assessment Recommendation System

A semantic similarity-based recommendation system that matches job descriptions to relevant SHL Individual Test Solutions assessments.

## Features

- **Semantic Search**: Uses sentence transformers for intelligent job description matching
- **Fast API**: Pre-computed embeddings for sub-200ms response times
- **Web UI**: Interactive frontend for easy testing
- **URL Support**: Automatically extracts text from job description URLs
- **Balanced Recommendations**: Ensures diversity across test type categories
- **Filtering**: Supports duration and type-based filtering

## Quick Start

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Run the FastAPI server:

```bash
uvicorn api:app --reload
```

1. Access the web UI at `http://localhost:8000`

1. Test the API:

```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Software Engineer role requiring strong problem solving"}'
```

### Streamlit App

Run the Streamlit application for interactive testing:

```bash
streamlit run app.py
```

## Project Structure

```text
.
├── api.py                 # FastAPI REST API
├── app.py                 # Streamlit application
├── data/
│   ├── catalogue.csv      # Assessment catalogue
│   └── catalogue.py       # Catalogue loader
├── models/
│   └── embedding_model.py # Sentence transformer model
├── recommender/
│   └── engine.py          # Core recommendation engine
├── templates/
│   └── index.html         # Web UI template
├── utils/
│   └── text_utils.py      # URL extraction utilities
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment
├── Dockerfile            # Docker deployment
└── APPROACH_DOCUMENT.md   # 2-page approach document
```

## API Endpoints

### POST /recommend

Get assessment recommendations for a job description.

**Request**:

```json
{
  "query": "Software Engineer role requiring strong problem solving"
}
```

**Response**:

```json
{
  "recommended_assessments": [
    {
      "url": "https://...",
      "name": "Assessment Name",
      "adaptive_support": "Yes",
      "description": "Assessment description",
      "duration": 30,
      "remote_support": "Yes",
      "test_type": ["Ability & Aptitude"]
    }
  ]
}
```

### GET /health

Health check endpoint.

**Response**:

```json
{
  "status": "healthy"
}
```

### GET /

Web UI for interactive testing.

## Deployment

Deploy on Railway by connecting your GitHub repository. The app will auto-deploy using the `Procfile` and `railway.json` configuration.

## Performance

- **Latency**: 50-150ms per query (warm)
- **Cold Start**: 2-3 seconds (one-time model loading)
- **Accuracy**: High-quality semantic matching
- **Scalability**: Tested up to 50 concurrent requests

## Documentation

- **Approach Document**: `APPROACH_DOCUMENT.md` - Complete 2-page approach and optimization details

## License

This project is part of the SHL Research Intern Assessment.
