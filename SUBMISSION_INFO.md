# Submission Information

## 3 URLs Required

### 1. API Endpoint
**URL**: `https://your-deployment-url.railway.app/recommend`

**Note**: Replace `your-deployment-url.railway.app` with your actual deployment URL after deploying to Railway, Render, Heroku, or your preferred platform.

**Example Request**:
```bash
curl -X POST "https://your-deployment-url.railway.app/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Software Engineer role requiring strong problem solving and programming skills"}'
```

**Example Response**:
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
      "test_type": ["Ability & Aptitude", "Knowledge & Skills"]
    }
  ]
}
```

**Health Check**: `GET https://your-deployment-url.railway.app/health`

### 2. GitHub Repository URL
**URL**: `https://github.com/RishiPramod/SHL-Research-Intern-Assessment`

This repository contains:
- Complete source code (`api.py`, `app.py`, `recommender/engine.py`, etc.)
- All experiments and evaluation code
- Streamlit application for testing
- FastAPI REST API implementation
- Data processing and model files
- Deployment configurations (Dockerfile, Procfile)
- Documentation

### 3. Web Application Frontend URL
**URL**: `https://your-deployment-url.railway.app/`

The FastAPI application serves a web UI at the root endpoint that provides:
- Interactive job description input
- Real-time assessment recommendations
- Detailed assessment information display
- User-friendly interface for testing

**Note**: Same base URL as the API endpoint - the web frontend is served by the same FastAPI application.

## 2-Page Approach Document

See `APPROACH_DOCUMENT.md` in the repository for the complete 2-page document outlining:
- Problem approach and solution architecture
- Initial implementation and baseline performance
- Optimization efforts and performance improvements
- Final performance metrics
- Technical decisions and future opportunities

## Quick Deployment Instructions

1. **Deploy to Railway** (Recommended):
   - Go to [railway.app](https://railway.app)
   - Create new project
   - Connect GitHub repository: `https://github.com/RishiPramod/SHL-Research-Intern-Assessment`
   - Railway will auto-detect and deploy
   - Get your deployment URL from Railway dashboard

2. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect GitHub repository
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

3. **Deploy to Heroku**:
   - Install Heroku CLI
   - Run: `heroku create your-app-name`
   - Run: `git push heroku main`

For detailed deployment instructions, see `DEPLOYMENT_GUIDE.md`.

## API Configuration (Appendix 2 Reference)

The API follows these specifications:
- **Endpoint**: `/recommend`
- **Method**: POST
- **Content-Type**: application/json
- **Request Body**: `{"query": "your job description text or URL"}`
- **Response**: JSON with `recommended_assessments` array
- **Health Check**: GET `/health` returns `{"status": "healthy"}`

## Testing

After deployment, test the API:
1. Visit the web frontend URL to use the interactive UI
2. Or use curl/Python to test the API endpoint directly
3. Check health endpoint to verify deployment
