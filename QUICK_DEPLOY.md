# 🚀 Quick Deployment Steps

## Your Repository
- **GitHub**: `https://github.com/AnshumohanAcharya/SHL-assessment`
- **Status**: ✅ Ready to deploy

---

## Step-by-Step: Deploy to Railway (5 minutes)

### Step 1: Sign Up/Login
1. Go to **https://railway.app**
2. Click **"Start a New Project"** or **"Login"**
3. Sign in with your **GitHub account**

### Step 2: Connect Repository
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub if prompted
4. Find and select: **`AnshumohanAcharya/SHL-assessment`**

### Step 3: Deploy
1. Railway will automatically:
   - Detect Python from `runtime.txt`
   - Install dependencies from `requirements.txt`
   - Use start command from `Procfile`
2. Wait 2-3 minutes for deployment to complete
3. You'll see build logs in real-time

### Step 4: Get Your URL
1. Once deployed, click on your service
2. Go to **Settings** tab
3. Scroll to **"Generate Domain"** section
4. Click **"Generate Domain"**
5. Your app is live! 🎉

**Your URLs will be:**
- **API**: `https://your-app-name.railway.app/recommend`
- **Web UI**: `https://your-app-name.railway.app/`
- **Health**: `https://your-app-name.railway.app/health`

---

## Alternative: Deploy to Render

### Step 1: Sign Up
1. Go to **https://render.com**
2. Sign up/login with GitHub

### Step 2: Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect repository: **`AnshumohanAcharya/SHL-assessment`**

### Step 3: Configure
- **Name**: `shl-recommender`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- **Plan**: Free (or paid if you prefer)

### Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait for deployment (3-5 minutes)
3. Your URL: `https://shl-recommender.onrender.com`

---

## Test Your Deployment

Once deployed, test with:

```bash
# Test API endpoint
curl -X POST "YOUR_URL/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "Software Engineer role requiring strong problem solving"}'

# Test health check
curl YOUR_URL/health

# Visit web UI
open YOUR_URL
```

---

## Update Submission Info

After deployment, update `SUBMISSION_INFO.md` with your actual URLs:

1. Replace `your-deployment-url.railway.app` with your actual domain
2. Update all three URLs:
   - API Endpoint
   - Web Frontend  
   - GitHub (already correct)

---

## Troubleshooting

**Build fails?**
- Check build logs in Railway/Render dashboard
- Ensure `requirements.txt` is correct
- Verify Python version in `runtime.txt` (3.10.13)

**App crashes?**
- Check logs for errors
- Verify `Procfile` start command
- Ensure port uses `$PORT` environment variable

**Slow first request?**
- Normal! First request loads the model (2-3 seconds)
- Subsequent requests are fast (50-150ms)

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Check deployment logs in your platform's dashboard
