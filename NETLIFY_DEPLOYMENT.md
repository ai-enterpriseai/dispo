# 🚀 Quick Netlify Deployment Guide

## TL;DR - Deploy to Netlify in 3 Steps

### Step 1: Deploy Backend (REQUIRED FIRST!)
Choose one platform for your Python Flask API:

**Option A: Railway (Recommended)**
1. Go to [railway.app](https://railway.app) → Deploy from GitHub
2. Select this repository
3. Configure:
   - Start Command: `python src/api/server.py`
   - Environment: `FLASK_ENV=production`
4. Get your URL: `https://your-app.railway.app`

**Option B: Render**
1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repository
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python src/api/server.py`
   - Environment: `FLASK_ENV=production`

### Step 2: Deploy Frontend to Netlify
1. Go to [netlify.com](https://netlify.com) → Add new site
2. Connect this GitHub repository
3. Configure build settings:
   - **Base directory**: `src/front`
   - **Build command**: `npm ci --legacy-peer-deps && npm run build`
   - **Publish directory**: `src/front/dist`
4. Add environment variable:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: Your backend URL from Step 1

### Step 3: Update CORS
Update `src/api/server.py` line ~20 to include your Netlify domain:
```python
CORS(app, 
     origins=[
         "http://localhost:5173", 
         "http://127.0.0.1:5173",
         "https://your-app.netlify.app"  # Add this line
     ])
```

## Files Created for Deployment
- ✅ `netlify.toml` - Netlify build configuration
- ✅ `Procfile` - Heroku deployment config  
- ✅ `deployment-guide.md` - Detailed deployment guide
- ✅ Updated `src/api/server.py` - Production-ready Flask server
- ✅ Updated `src/front/src/context/DataContext.tsx` - Environment variable support

## Test Your Deployment
1. Backend: Visit `https://your-backend.railway.app/api/status`
2. Frontend: Visit `https://your-app.netlify.app`

## Need Help?
- Check `deployment-guide.md` for detailed instructions
- Run `node scripts/prepare-netlify-deploy.js` for deployment checklist 