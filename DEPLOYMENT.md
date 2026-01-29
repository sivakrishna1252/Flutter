# Diet Planner - Deployment Guide

## 📋 Pre-Deployment Checklist

### 1. Environment Setup

Before pushing to Git and deploying, make sure you have:

1. ✅ Created `.env.example` file (template for environment variables)
2. ✅ Updated `.gitignore` to exclude sensitive files
3. ✅ Updated `settings.py` to use environment variables
4. ✅ Your actual `.env` file is NOT committed to Git

### 2. Verify Git Status

Check what files will be committed:

```bash
git status
```

**Important**: Make sure `config/.env` is NOT listed in files to be committed!

---

## 🚀 Deployment Steps

### Step 1: Initialize Git (if not already done)

```bash
git init
```

### Step 2: Add Files to Git

```bash
git add .
```

### Step 3: Commit Changes

```bash
git commit -m "Initial commit - Diet Planner API"
```

### Step 4: Create GitHub Repository

1. Go to [GitHub](https://github.com)
2. Click "New Repository"
3. Name it: `diet-planner`
4. **DO NOT** initialize with README (we already have code)
5. Click "Create Repository"

### Step 5: Push to GitHub

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/diet-planner.git

# Push code
git branch -M main
git push -u origin main
```

---

## 🌐 Deployment Options

### Option 1: Deploy to Render (Recommended - Free Tier Available)

1. **Create Account**: Go to [Render.com](https://render.com)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `diet-planner` repository

3. **Configure Service**:
   - **Name**: `diet-planner-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Instance Type**: Free

4. **Add Environment Variables** (in Render Dashboard):
   ```
   SECRET_KEY=your-production-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-app-name.onrender.com
   OPENAI_API_KEY=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
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL_NAME=nvidia/nemotron-3-nano-30b-a3b:free
   OPENAI_IMAGE_MODEL_NAME=stabilityai/stable-diffusion-xl-base-1.0
   ```

5. **Deploy**: Click "Create Web Service"

---

### Option 2: Deploy to Railway

1. **Create Account**: Go to [Railway.app](https://railway.app)

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `diet-planner`

3. **Add Environment Variables**:
   - Go to "Variables" tab
   - Add all variables from `.env.example`
   - Set `DEBUG=False` for production

4. **Deploy**: Railway will auto-deploy

---

### Option 3: Deploy to PythonAnywhere

1. **Create Account**: Go to [PythonAnywhere.com](https://www.pythonanywhere.com)

2. **Upload Code**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/diet-planner.git
   ```

3. **Create Virtual Environment**:
   ```bash
   cd diet-planner
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Web App**:
   - Go to "Web" tab
   - Add new web app
   - Choose "Manual configuration"
   - Set WSGI file path

5. **Add Environment Variables**:
   - Create `.env` file in `/home/yourusername/diet-planner/config/`
   - Copy values from your local `.env`

---

## 📝 Important Notes

### Production Settings

For production deployment, update these in your environment variables:

```env
SECRET_KEY=generate-a-new-secret-key-for-production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### Generate New Secret Key

Run this in Python to generate a new secret key:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Database Migration

After deployment, run migrations:

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Static Files

For production, you may need to configure static files:

```bash
python manage.py collectstatic
```

---

## 🔒 Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] `SECRET_KEY` is different in production
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` is properly configured
- [ ] Database is backed up regularly
- [ ] HTTPS is enabled (most platforms do this automatically)

---

## 🐛 Troubleshooting

### Issue: "DisallowedHost" Error
**Solution**: Add your domain to `ALLOWED_HOSTS` environment variable

### Issue: Static files not loading
**Solution**: Run `python manage.py collectstatic` and configure `STATIC_ROOT`

### Issue: Database errors
**Solution**: Run `python manage.py migrate`

---

## 📞 Support

If you encounter issues:
1. Check deployment platform logs
2. Verify all environment variables are set
3. Ensure `requirements.txt` includes all dependencies

---

## ✅ Post-Deployment

After successful deployment:

1. Test API endpoints
2. Create superuser account
3. Test authentication flow
4. Monitor logs for errors
5. Set up monitoring/alerts (optional)

Your API will be available at: `https://your-app-name.platform.com`

---

**Good luck with your deployment! 🚀**
