# Deploy to Heroku - Step by Step Guide

Heroku is the **easiest option** that doesn't require downloading any software to your computer. Everything is done through Git and web browser!

## Prerequisites:
- ✅ Your code is already on GitHub: `https://github.com/sfc-gh-bnam/boot-camp-class-list-bn.git`
- ✅ You have a GitHub account
- ✅ You'll need to create a free Heroku account

## Step 1: Create Heroku Account

1. Go to: https://www.heroku.com/
2. Click "Sign up" (it's free)
3. Create your account

## Step 2: Install Heroku CLI (Optional - Can also use web interface)

**Option A: Use Heroku Dashboard (Web-based, No Download)**
- You can deploy directly from GitHub using Heroku's web dashboard
- No CLI installation needed!

**Option B: Install Heroku CLI (If allowed by company)**
- Download from: https://devcenter.heroku.com/articles/heroku-cli
- Or use web-based deployment (recommended if CLI blocked)

## Step 3: Deploy via Heroku Dashboard (Web-based - Recommended)

1. **Login to Heroku**: https://dashboard.heroku.com/

2. **Create New App**:
   - Click "New" → "Create new app"
   - Choose an app name (e.g., `boot-camp-dashboard-bn`)
   - Select region (United States or Europe)
   - Click "Create app"

3. **Connect to GitHub**:
   - In your app dashboard, go to "Deploy" tab
   - Under "Deployment method", select "GitHub"
   - Click "Connect to GitHub" and authorize Heroku
   - Search for your repository: `boot-camp-class-list-bn`
   - Click "Connect"

4. **Configure Buildpacks**:
   - Go to "Settings" tab
   - Click "Add buildpack"
   - Select "Python" → "Save changes"

5. **Deploy**:
   - Go back to "Deploy" tab
   - Under "Manual deploy", select `main` branch
   - Click "Deploy Branch"
   - Wait for deployment to complete (2-3 minutes)

6. **Your App is Live!** keywords:
   - Click "Open app" button
   - Your app URL will be: `https://your-app-name.herokuapp.com`

## Step 4: Make it Auto-Deploy (Optional)

- Under "Automatic deploys", select `main` branch
- Click "Enable Automatic Deploys"
- Now every time you push to GitHub, Heroku will auto-deploy!

## Step 5: Update Your Files on GitHub

Before deploying, make sure all necessary files are committed and pushed:

```bash
cd "/Users/bnam/Code Development/streamlit"
git add Procfile setup.sh requirements.txt employee_dashboard_fixed.py
git commit -m "Add Heroku deployment files"
git push origin main
```

## Important Notes:

- ⚠️ **Free tier**: Heroku free tier has been discontinued, but there's a low-cost option ($5/month for Eco dyno)
- 🔄 **Auto-deployange**: Set up automatic deploys from GitHub for convenience
- 📦 **File size**: Make sure your files are under Heroku's limits (100MB per file)
- 🔒 **Security**: The app will be publicly accessible at the Heroku URL

## Troubleshooting:

If deployment fails:
1. Check the "Activity" tab in Heroku dashboard for error logs
2. Verify `requirements.txt` has all dependencies
3. Make sure `Procfile` and `setup.sh` are in the root directory
4. Check that `employee_dashboard_fixed.py` is the main file

## Alternative: Railway.app (Similar to Heroku, $5/month)

If Heroku doesn't work, try Railway.app:
- Go to: https://railway.app/
- Connect GitHub repo
- Auto-detects Python/Streamlit
- Similar process to Heroku

