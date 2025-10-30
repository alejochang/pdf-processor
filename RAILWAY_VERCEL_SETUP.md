# Railway + Vercel Deployment - Step-by-Step Guide

Complete guide for deploying the PDF Processor with Railway (backend) and Vercel (frontend).

---

## 📋 Prerequisites

- [x] GitHub account
- [x] Railway account (free): https://railway.app
- [x] Vercel account (free): https://vercel.com
- [x] Gemini API key
- [x] Mistral API key

---

## Part 1: Deploy Backend on Railway

### Step 1: Sign Up / Log In

1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose: `alejochang/pdf-processor`
4. Railway will create a new project

### Step 3: Add Redis Database

1. In your Railway project dashboard, click **"New"**
2. Select **"Database"** → **"Add Redis"**
3. Railway automatically creates a Redis instance
4. Note: The `REDIS_URL` will be available as `${{Redis.REDIS_URL}}`

### Step 4: Configure Backend Service

1. Click **"New"** → **"GitHub Repo"**
2. Select `alejochang/pdf-processor` again
3. Railway will create a service

#### Configure Service Settings:

1. Click on the service card
2. Go to **"Settings"** tab:
   - **Service Name**: `backend`
   - **Root Directory**: `backend`
   - **Start Command**: (leave empty, uses Dockerfile)
   - **Watch Paths**: `backend/**`

3. Go to **"Variables"** tab and add:

   ```
   REDIS_URL=${{Redis.REDIS_URL}}
   GOOGLE_API_KEY=AIzaSyDxQWdpHhxe0SckdBArq19pStScZc7iMK0
   MISTRAL_API_KEY=0mmezs4ZhtCrOwBkEgLQ58kNl8O1AFjO
   MAX_FILE_SIZE_MB=25
   PORT=8000
   ```

   **Important**: Replace the API keys with your actual keys if different!

4. Click **"Deploy"**

### Step 5: Add Worker Service

1. Click **"New"** → **"GitHub Repo"**
2. Select `alejochang/pdf-processor` again
3. Railway creates another service

#### Configure Worker Settings:

1. Click on the worker service card
2. Go to **"Settings"** tab:
   - **Service Name**: `worker`
   - **Root Directory**: `backend`
   - **Start Command**: `python -m app.worker`
   - **Watch Paths**: `backend/**`

3. Go to **"Variables"** tab and add:

   ```
   REDIS_URL=${{Redis.REDIS_URL}}
   GOOGLE_API_KEY=AIzaSyDxQWdpHhxe0SckdBArq19pStScZc7iMK0
   MISTRAL_API_KEY=0mmezs4ZhtCrOwBkEgLQ58kNl8O1AFjO
   ```

4. Click **"Deploy"**

### Step 6: Get Backend URL

1. Click on the **backend** service
2. Go to **"Settings"** → **"Networking"**
3. Click **"Generate Domain"**
4. Copy your domain (e.g., `https://pdf-processor-production-c5ad.up.railway.app`)

**Save this URL - you'll need it for Vercel!**

### Step 7: Verify Backend Deployment

1. Wait for deployment to complete (~2-3 minutes)
2. Visit: `https://YOUR-RAILWAY-URL.railway.app/health`
3. You should see:
   ```json
   {
     "status": "healthy",
     "redis": "connected",
     "version": "1.0.0"
   }
   ```

✅ **Backend deployment complete!**

---

## Part 2: Deploy Frontend on Vercel

### Step 1: Sign Up / Log In

1. Go to https://vercel.com
2. Click "Sign Up" → "Continue with GitHub"
3. Authorize Vercel to access your GitHub

### Step 2: Import Project

1. Click **"Add New..."** → **"Project"**
2. Find `alejochang/pdf-processor` in the list
3. Click **"Import"**

### Step 3: Configure Project Settings

**IMPORTANT: Configure these settings carefully!**

#### Project Configuration:

- **Framework Preset**: Next.js (auto-detected ✓)
- **Root Directory**: Click **"Edit"** → Select `frontend-nextjs`
- **Build Command**: `npm run build` (default, no change needed)
- **Output Directory**: `.next` (default, no change needed)
- **Install Command**: `npm install` (default, no change needed)

#### Environment Variables:

Click **"Environment Variables"** and add:

**Key**: `NEXT_PUBLIC_API_URL`
**Value**: `https://YOUR-RAILWAY-BACKEND-URL.railway.app`

Example: `https://pdf-processor-production-c5ad.up.railway.app`

**Important Notes:**
- Do NOT include `/api` at the end
- Do NOT include trailing slash
- Make sure it's your Railway backend URL from Step 6 above

### Step 4: Deploy

1. Click **"Deploy"**
2. Vercel will:
   - Clone your repository
   - Install dependencies
   - Build Next.js app
   - Deploy to global CDN

This takes ~2-3 minutes.

### Step 5: Verify Frontend Deployment

1. Once complete, Vercel shows your deployment URL
2. Click **"Visit"** or go to: `https://your-project.vercel.app`
3. You should see the PDF Processor UI!

✅ **Frontend deployment complete!**

---

## Part 3: Update Backend CORS (Important!)

Your backend needs to allow requests from your Vercel frontend.

### Option A: Via GitHub (Recommended)

1. Go to your repository: `github.com/alejochang/pdf-processor`
2. Navigate to: `backend/app/main.py`
3. Click **"Edit"** (pencil icon)
4. Find the CORS middleware section (around line 25):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
    ],
```

5. Add your Vercel URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "https://your-project.vercel.app",  # Add this line
    ],
```

6. Commit changes
7. Railway will auto-redeploy the backend

### Option B: Via Local Git

```bash
# Edit backend/app/main.py
nano backend/app/main.py

# Add your Vercel URL to allow_origins list

# Commit and push
git add backend/app/main.py
git commit -m "feat: add Vercel URL to CORS allow_origins"
git push origin main
```

Railway will detect the push and redeploy automatically.

---

## 🎉 Deployment Complete!

Your application is now live!

**Frontend**: `https://your-project.vercel.app`
**Backend API**: `https://your-railway-backend.railway.app`
**API Docs**: `https://your-railway-backend.railway.app/docs`

---

## 🧪 Test Your Deployment

### 1. Visit Frontend

Go to: `https://your-project.vercel.app`

### 2. Upload a PDF

1. Click or drag a PDF file
2. Select a parser (try "Gemini")
3. Click "Upload and Process"

### 3. Monitor Processing

- The job should appear in the "Processing Jobs" list
- Status will update: pending → processing → completed
- Click "View Results" when complete

### 4. Check Backend

Visit: `https://your-railway-backend.railway.app/docs`

Try the API endpoints directly!

---

## 📊 Monitoring Your Deployment

### Railway Dashboard

1. Go to your Railway project
2. Click on each service to see:
   - **Deployments**: Build logs and history
   - **Metrics**: CPU, Memory, Network usage
   - **Logs**: Live application logs

**Useful Railway CLI commands:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# View logs
railway logs

# SSH into service
railway shell
```

### Vercel Dashboard

1. Go to your Vercel project
2. See:
   - **Deployments**: Build history
   - **Analytics**: Page views, performance
   - **Logs**: Runtime logs

---

## 💰 Cost & Limits

### Railway Free Tier

- **$5 free credits/month**
- **500 execution hours/month**
- Enough for development/testing!

**Exceeding free tier?**
- Add a credit card for pay-as-you-go
- ~$5-20/month for small projects

### Vercel Free Tier (Hobby)

- **100 GB bandwidth/month**
- **Unlimited deployments**
- **Free HTTPS/SSL**
- **No credit card required**

**Exceeding free tier?**
- Upgrade to Pro: $20/month

---

## 🔧 Common Issues & Solutions

### Issue 1: Frontend Shows "Failed to fetch"

**Cause**: CORS not configured or wrong API URL

**Solution**:
1. Check `NEXT_PUBLIC_API_URL` in Vercel environment variables
2. Ensure backend CORS includes your Vercel URL
3. Redeploy both services

### Issue 2: Worker Not Processing Jobs

**Cause**: Worker service not running or Redis connection issue

**Solution**:
1. Check Railway worker service logs
2. Verify `REDIS_URL` is set correctly
3. Restart worker service

### Issue 3: "Module not found" Errors

**Cause**: Dependencies not installed or build cache issue

**Solution**:
```bash
# In Vercel:
# Settings → General → Clear Build Cache → Redeploy

# In Railway:
# Service → Settings → Clear Build Cache
```

### Issue 4: Build Fails in Vercel

**Cause**: Incorrect root directory or missing dependencies

**Solution**:
1. Verify Root Directory is `frontend-nextjs`
2. Check build logs for specific errors
3. Ensure `package.json` and `package-lock.json` exist

### Issue 5: API Requests Timeout

**Cause**: Railway backend sleeping (free tier) or overloaded

**Solution**:
1. Railway free tier services may sleep after inactivity
2. First request wakes service (may take 30s)
3. Subsequent requests are fast
4. Upgrade to prevent sleeping

---

## 🔄 Updating Your Deployment

### Auto-Deploy from GitHub

Both Railway and Vercel auto-deploy when you push to `main`:

```bash
# Make your changes locally
git add .
git commit -m "feat: your changes"
git push origin main

# Railway and Vercel will automatically deploy!
```

### Manual Redeploy

**Railway:**
1. Go to service → Deployments
2. Click "..." → "Redeploy"

**Vercel:**
1. Go to project → Deployments
2. Find deployment → Click "..." → "Redeploy"

---

## 🎯 Next Steps

### 1. Custom Domain (Optional)

**Vercel:**
1. Vercel → Project → Settings → Domains
2. Add your domain
3. Configure DNS (Vercel provides instructions)

**Railway:**
1. Railway → Service → Settings → Networking
2. Add custom domain
3. Configure DNS

### 2. Environment-Specific Configs

Create different environments:
- `main` branch → Production
- `dev` branch → Staging

### 3. Monitoring & Alerts

**Railway:**
- Enable notifications in Settings
- Get alerts for failures

**Vercel:**
- Enable deployment notifications
- Integrate with Slack/Discord

### 4. Performance Optimization

- Enable Vercel Analytics
- Use Railway Metrics to identify bottlenecks
- Consider caching strategies

---

## 📞 Support

### Railway
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Support: help@railway.app

### Vercel
- Docs: https://vercel.com/docs
- Discord: https://vercel.com/discord
- Support: support@vercel.com

### This Project
- GitHub Issues: https://github.com/alejochang/pdf-processor/issues

---

## ✅ Deployment Checklist

- [ ] Railway account created
- [ ] Vercel account created
- [ ] Backend deployed on Railway
- [ ] Worker deployed on Railway
- [ ] Redis added and connected
- [ ] Backend URL copied
- [ ] Frontend deployed on Vercel
- [ ] `NEXT_PUBLIC_API_URL` set in Vercel
- [ ] CORS updated in backend
- [ ] Both services redeployed
- [ ] Test upload works
- [ ] PDF processing completes
- [ ] Results display correctly

---

**Congratulations! Your PDF Processor is live! 🎉**
