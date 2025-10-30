# PDF Processor - Deployment Quick Start

Choose your deployment method and get started in minutes!

---

## 🚀 Super Quick Options

### Option 1: AWS EC2 (Simplest, Full Control)

**Time to deploy: ~10 minutes**

```bash
# 1. Launch Ubuntu 22.04 EC2 instance (t3.small or larger)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 3. Run one-line installer
curl -sSL https://raw.githubusercontent.com/alejochang/pdf-processor/main/deploy-ec2-simple.sh | bash
```

**Access:** `http://YOUR_EC2_IP:3000`

**Cost:** ~$15-30/month

---

### Option 2: Railway + Vercel (Zero Config, Git-Based)

**Time to deploy: ~5 minutes**

#### Backend on Railway:

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select `alejochang/pdf-processor`
4. Add Redis: Click "New" → "Database" → "Redis"
5. Add environment variables:
   ```
   REDIS_URL=${{Redis.REDIS_URL}}
   GOOGLE_API_KEY=your_key
   MISTRAL_API_KEY=your_key
   MAX_FILE_SIZE_MB=25
   ```
6. Set Root Directory: `backend`
7. Copy your Railway URL

#### Frontend on Vercel:

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project" → Import `alejochang/pdf-processor`
3. Root Directory: `frontend-nextjs`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-app.railway.app
   ```
5. Deploy!

**Cost:** Free tier available, or ~$5-20/month

---

### Option 3: Render (All-in-One)

**Time to deploy: ~7 minutes**

1. Go to [render.com](https://render.com)
2. Click "New" → "Blueprint"
3. Connect GitHub repo
4. Select `alejochang/pdf-processor`
5. Render auto-deploys from `render.yaml`
6. Add API keys in environment variables

**Cost:** Free tier or $7/service/month

---

## 📋 Detailed Deployment Guide

For complete instructions including:
- AWS ECS deployment
- Nginx reverse proxy setup
- HTTPS/SSL configuration
- CI/CD pipelines
- Monitoring & logging
- Troubleshooting

See **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

---

## 🔑 Required API Keys

You need two API keys:

1. **Google Gemini API Key**
   - Get it from: https://makersuite.google.com/app/apikey
   - Free tier: 15 requests/minute

2. **Mistral API Key**
   - Get it from: https://console.mistral.ai/
   - Free tier: Limited requests

---

## 📊 Deployment Comparison

| Method | Setup Time | Cost | Auto-Deploy | HTTPS | Recommended For |
|--------|-----------|------|-------------|-------|-----------------|
| **AWS EC2** | 10 min | $15-30/mo | No | Manual | Learning, full control |
| **Railway + Vercel** | 5 min | $0-20/mo | Yes | Auto | Quick prototype |
| **Render** | 7 min | $0-28/mo | Yes | Auto | Simple deployment |
| **AWS ECS** | 30 min | $30-70/mo | No | Manual | Production, scale |

---

## ✅ Post-Deployment Checklist

After deployment, verify:

- [ ] Frontend is accessible
- [ ] Backend API responds at `/health`
- [ ] Can upload a PDF file
- [ ] PDF processing completes successfully
- [ ] Results are displayed correctly
- [ ] HTTPS is enabled (if production)
- [ ] API keys are not exposed in logs
- [ ] CORS is configured for your domain

---

## 🆘 Quick Troubleshooting

### Frontend can't connect to backend
```bash
# Check NEXT_PUBLIC_API_URL in .env
# Should point to your backend URL
```

### Worker not processing jobs
```bash
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Out of memory
```bash
# Increase EC2 instance size
# Or add swap:
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📞 Support

- **Full Documentation**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **GitHub Issues**: https://github.com/alejochang/pdf-processor/issues
- **Email**: your-email@example.com

---

## 🎯 Recommended: AWS EC2 for First Deployment

If you're new to deployment, we recommend AWS EC2 because:
- Simple setup with one script
- Full control over the environment
- Easy to debug and monitor
- Good balance of cost and features
- Complete Docker Compose experience

Just run:
```bash
curl -sSL https://raw.githubusercontent.com/alejochang/pdf-processor/main/deploy-ec2-simple.sh | bash
```

---

**Ready to deploy? Choose your method above and get started!**
