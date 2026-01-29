# 🎯 Git Push & Deployment - Quick Guide

## ✅ What I've Done For You

I've prepared your project for Git and deployment by:

1. ✅ **Created `.gitignore`** - Protects sensitive files from being pushed to Git
2. ✅ **Created `.env.example`** - Template for environment variables (safe to share)
3. ✅ **Updated `settings.py`** - Now uses environment variables securely
4. ✅ **Added production dependencies** - `gunicorn` and `whitenoise` for deployment
5. ✅ **Created `README.md`** - Professional project documentation
6. ✅ **Created `DEPLOYMENT.md`** - Step-by-step deployment guide

## 🔒 Security Status

Your sensitive data is now protected:
- ✅ `config/.env` is in `.gitignore` (won't be pushed to Git)
- ✅ `SECRET_KEY` uses environment variables
- ✅ API keys are loaded from environment variables
- ✅ Database file is excluded from Git

## 🚀 Next Steps - Push to Git

### Step 1: Check Git Status (Optional)
```bash
git status
```

### Step 2: Add All Files
```bash
git add .
```

### Step 3: Commit Changes
```bash
git commit -m "Prepare project for deployment with environment variables"
```

### Step 4: Create GitHub Repository
1. Go to https://github.com
2. Click "New Repository"
3. Name: `diet-planner`
4. **DO NOT** initialize with README
5. Click "Create Repository"

### Step 5: Push to GitHub
```bash
# Add your GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/diet-planner.git

# Push code
git branch -M main
git push -u origin main
```

## 🌐 Deploy Your Project

After pushing to GitHub, you can deploy to:

### Option 1: Render (Recommended - Free)
1. Go to https://render.com
2. Sign up/Login
3. Click "New +" → "Web Service"
4. Connect GitHub and select `diet-planner`
5. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn config.wsgi:application`
6. Add environment variables (copy from `.env.example`)
7. Click "Create Web Service"

### Option 2: Railway
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select `diet-planner`
4. Add environment variables
5. Deploy automatically

## 📝 Important Environment Variables for Production

When deploying, set these environment variables:

```env
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
OPENAI_API_KEY=<your-actual-api-key>
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL_NAME=nvidia/nemotron-3-nano-30b-a3b:free
OPENAI_IMAGE_MODEL_NAME=stabilityai/stable-diffusion-xl-base-1.0
```

## 🔑 Generate New Secret Key for Production

Run this in Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use this command:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## ✅ Verification Checklist

Before pushing:
- [ ] `.env` file is NOT showing in `git status`
- [ ] `.gitignore` includes `.env` and `config/.env`
- [ ] `.env.example` exists (this is safe to push)
- [ ] `settings.py` uses `os.getenv()` for sensitive values

## 🎉 You're Ready!

Your project is now:
- ✅ Secure (no secrets in Git)
- ✅ Production-ready
- ✅ Easy to deploy
- ✅ Well-documented

Just follow the steps above to push to Git and deploy!

---

**Need help? Check `DEPLOYMENT.md` for detailed instructions!**
