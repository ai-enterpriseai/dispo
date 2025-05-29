# 🚛 Deployment Guide: Truck Dispatch Optimization System

## Overview

This application has two components:
- **Frontend**: React app (can be deployed to Netlify)
- **Backend**: Python Flask API (needs separate deployment)

## Option 1: Frontend on Netlify + Backend on Railway/Render (Recommended)

### Step 1: Deploy Backend

#### Option A: Deploy to Railway
1. Create account at [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Deploy the backend with these settings:
   ```
   Root Directory: /
   Build Command: pip install -r requirements.txt
   Start Command: python src/api/server.py
   ```
4. Set environment variables:
   ```
   PORT=5000
   PYTHONPATH=/app/src
   ```

#### Option B: Deploy to Render
1. Create account at [render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repository
4. Configure:
   ```
   Root Directory: /
   Build Command: pip install -r requirements.txt
   Start Command: python src/api/server.py
   ```

#### Option C: Deploy to Heroku
1. Create `Procfile` in root:
   ```
   web: python src/api/server.py
   ```
2. Update `src/api/server.py` to use environment PORT:
   ```python
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5000))
       app.run(debug=False, port=port, host='0.0.0.0')
   ```

### Step 2: Update Frontend API URLs

Update the API base URL in your React app to point to your deployed backend:

1. Create `src/front/.env.production`:
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   ```

2. Update your API calls to use the environment variable:
   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
   ```

### Step 3: Deploy Frontend to Netlify

#### Method A: Netlify Dashboard
1. Sign up at [netlify.com](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Connect your GitHub repository
4. Configure build settings:
   - **Base directory**: `src/front`
   - **Build command**: `npm ci --legacy-peer-deps && npm run build`
   - **Publish directory**: `src/front/dist`
5. Add environment variables:
   - `VITE_API_BASE_URL`: Your deployed backend URL
6. Deploy!

#### Method B: Netlify CLI
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Build the frontend
cd src/front
npm install --legacy-peer-deps
npm run build

# Deploy
netlify deploy --prod --dir=dist
```

#### Method C: Git Integration
1. Push this repository to GitHub
2. The `netlify.toml` file will automatically configure the build
3. Connect the repository in Netlify dashboard

## Option 2: Netlify Functions (Serverless)

Convert the Flask backend to Netlify Functions (requires significant refactoring):

### Step 1: Create Netlify Functions

Create `netlify/functions/optimize.js`:
```javascript
// This would require converting Python logic to Node.js
// Or using child_process to run Python scripts
exports.handler = async (event, context) => {
  // Handle optimization requests
};
```

### Step 2: Update Build Configuration

Update `netlify.toml`:
```toml
[build]
  functions = "netlify/functions"
  command = "cd src/front && npm ci --legacy-peer-deps && npm run build"
  publish = "src/front/dist"

[functions]
  node_bundler = "nft"
```

**Note**: This approach is complex and not recommended for this Python-heavy application.

## Option 3: Static Export (Limited Functionality)

For demo purposes only - remove backend dependencies:

1. Modify the React app to use mock data instead of API calls
2. Remove all API integrations
3. Deploy as pure static site

## Recommended Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Netlify       │    │   Railway/Render │
│   (Frontend)    │◄──►│   (Backend API)  │
│   React App     │    │   Flask + PuLP   │
└─────────────────┘    └──────────────────┘
        │                       │
        │                       │
        ▼                       ▼
  ┌──────────┐            ┌──────────┐
  │   CDN    │            │ Database │
  │ (Static) │            │   (CSV)  │
  └──────────┘            └──────────┘
```

## Environment Variables

### Frontend (.env.production)
```
VITE_API_BASE_URL=https://your-backend.railway.app
```

### Backend (Railway/Render)
```
PORT=5000
PYTHONPATH=/app/src
FLASK_ENV=production
```

## Pre-Deployment Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend environment variables updated
- [ ] CORS configured for production domains
- [ ] Build process tested locally
- [ ] API endpoints tested with production URLs
- [ ] Error handling for failed API calls

## Troubleshooting

### Common Issues

1. **CORS Errors**: Update Flask CORS settings to include your Netlify domain
2. **Build Failures**: Check Node.js version and dependencies
3. **API Connection**: Verify backend URL and health endpoint
4. **File Paths**: Ensure relative paths work in production

### Backend CORS Update

Update `src/api/server.py`:
```python
CORS(app, 
     origins=[
         "http://localhost:5173", 
         "http://127.0.0.1:5173",
         "https://your-app.netlify.app"  # Add your Netlify domain
     ],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True
)
```

## Cost Considerations

- **Netlify**: Free tier for frontend hosting
- **Railway**: ~$5/month for backend
- **Render**: Free tier available, then ~$7/month
- **Heroku**: ~$7/month (no free tier)

## Next Steps

1. Choose backend hosting platform
2. Deploy backend first
3. Update frontend configuration
4. Deploy frontend to Netlify
5. Test end-to-end functionality 