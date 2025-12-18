# Deployment Guide & URLs

## Deployment URLs

### 1. API Endpoint
**URL**: `https://your-deployment-url.railway.app/recommend` (or your deployed URL)

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
      "url": "https://...",
      "name": "Assessment Name",
      "adaptive_support": "Yes/No",
      "description": "Assessment description",
      "duration": 30,
      "remote_support": "Yes/No",
      "test_type": ["Ability & Aptitude", "Knowledge & Skills"]
    }
  ]
}
```

**Health Check**: `GET https://your-deployment-url.railway.app/health`

### 2. GitHub Repository
**URL**: `https://github.com/RishiPramod/SHL-Research-Intern-Assessment`

This repository contains:
- Complete source code
- All experiments and evaluation code
- Streamlit app for testing (`app.py`)
- FastAPI implementation (`api.py`)
- Data processing scripts
- Requirements and deployment configurations

### 3. Web Application Frontend
**URL**: `https://your-deployment-url.railway.app/` (same as API, serves HTML frontend)

The FastAPI application serves a web UI at the root endpoint (`/`) that allows users to:
- Enter job descriptions or JD URLs
- Get recommendations with a user-friendly interface
- View assessment details including URLs, descriptions, test types, and duration

## Deployment Options

### Option 1: Railway (Recommended)
1. Sign up at [railway.app](https://railway.app)
2. Create new project
3. Connect GitHub repository
4. Railway will auto-detect the Python app
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
7. Deploy!

### Option 2: Render
1. Sign up at [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repository
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
6. Deploy!

### Option 3: Heroku
1. Install Heroku CLI
2. Run: `heroku create your-app-name`
3. Run: `git push heroku main`
4. Heroku will use the `Procfile` automatically

### Option 4: Docker
1. Build: `docker build -t shl-recommender .`
2. Run: `docker run -p 8000:8000 shl-recommender`
3. Access: `http://localhost:8000`

## Environment Variables
No environment variables required for basic deployment. The app uses:
- Default model: `all-MiniLM-L6-v2` (downloads automatically)
- Catalogue: `data/catalogue.csv` (included in repo)

## Testing the API

### Using curl:
```bash
curl -X POST "https://your-deployment-url.railway.app/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Java developer with strong problem-solving skills"}'
```

### Using Python:
```python
import requests

response = requests.post(
    "https://your-deployment-url.railway.app/recommend",
    json={"query": "Software Engineer role requiring strong problem solving"}
)
print(response.json())
```

## Notes
- First request may take 2-3 seconds (cold start for model loading)
- Subsequent requests are fast (50-150ms)
- The API supports CORS for frontend integration
- Health check endpoint available at `/health`
