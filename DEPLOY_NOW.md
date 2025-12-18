# Quick Deployment Guide

## Option 1: Railway (Recommended - Easiest)

### Steps:
1. Go to https://railway.app and sign up/login with GitHub
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository: `AnshumohanAcharya/SHL-assessment`
5. Railway will auto-detect Python and deploy
6. Once deployed, click on your service → Settings → Generate Domain
7. Your app will be live at: `https://your-app-name.railway.app`

**No configuration needed** - Railway auto-detects:
- Python runtime from `runtime.txt`
- Start command from `Procfile`
- Dependencies from `requirements.txt`

---

## Option 2: Render (Alternative)

### Steps:
1. Go to https://render.com and sign up/login with GitHub
2. Click "New +" → "Web Service"
3. Connect your repository: `AnshumohanAcharya/SHL-assessment`
4. Configure:
   - **Name**: `shl-recommender` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Click "Create Web Service"
6. Your app will be live at: `https://your-app-name.onrender.com`

---

## Option 3: Fly.io (Fast & Global)

### Steps:
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Run: `fly auth login`
3. Run: `fly launch` (in your project directory)
4. Follow prompts - Fly will auto-detect settings
5. Your app will be live at: `https://your-app-name.fly.dev`

---

## Option 4: Local Testing First

Test locally before deploying:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the server
uvicorn api:app --host 0.0.0.0 --port 8000
```

Then visit: http://localhost:8000

---

## After Deployment

Once deployed, update `SUBMISSION_INFO.md` with your actual URLs:

1. **API Endpoint**: `https://your-app-name.railway.app/recommend`
2. **Web Frontend**: `https://your-app-name.railway.app/`
3. **GitHub**: `https://github.com/AnshumohanAcharya/SHL-assessment`

## Testing Your Deployment

```bash
# Test API
curl -X POST "https://your-app-name.railway.app/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Software Engineer role requiring strong problem solving"}'

# Test Health
curl https://your-app-name.railway.app/health
```
