# PDF Processor - Deployment Guide

Complete deployment instructions for multiple platforms.

---

## 🚀 Quick Deployment Options

| Platform | Complexity | Cost | Best For |
|----------|------------|------|----------|
| **AWS EC2 + Docker** | Low | ~$20/month | Full control, simple setup |
| **Railway + Vercel** | Very Low | Free tier available | Git-based, auto-deploy |
| **AWS ECS** | Medium | ~$30/month | Production, scalability |
| **Render** | Very Low | Free tier available | Quick prototype |

---

## Option 1: AWS EC2 with Docker Compose (Recommended)

### Prerequisites
- AWS account
- Basic SSH knowledge
- Domain name (optional)

### Step 1: Launch EC2 Instance

1. **Go to AWS EC2 Console**
   - Choose "Launch Instance"
   - Name: `pdf-processor`

2. **Select AMI**
   - Ubuntu Server 22.04 LTS (Free tier eligible)

3. **Choose Instance Type**
   - **Development**: t2.micro (free tier) or t3.small
   - **Production**: t3.medium (2 vCPU, 4GB RAM)

4. **Configure Security Group**
   - SSH (22): Your IP
   - HTTP (80): 0.0.0.0/0
   - HTTPS (443): 0.0.0.0/0
   - Custom TCP (3000): 0.0.0.0/0
   - Custom TCP (8000): 0.0.0.0/0

5. **Create/Select Key Pair**
   - Download `.pem` file
   - Save as `pdf-processor-key.pem`

6. **Storage**
   - 20GB gp3 (recommended)

### Step 2: Connect to EC2

```bash
# Set permissions on key file
chmod 400 pdf-processor-key.pem

# Connect to instance
ssh -i pdf-processor-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 3: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose git

# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Step 4: Clone and Configure

```bash
# Clone repository
git clone https://github.com/alejochang/pdf-processor.git
cd pdf-processor

# Get public IP for API URL
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Create .env file
cat > .env << EOF
REDIS_URL=redis://redis:6379
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
MISTRAL_API_KEY=YOUR_MISTRAL_API_KEY
MAX_FILE_SIZE_MB=25
UPLOAD_DIR=/app/uploads
NEXT_PUBLIC_API_URL=http://$PUBLIC_IP:8000
EOF

# Important: Replace YOUR_GEMINI_API_KEY and YOUR_MISTRAL_API_KEY
nano .env  # Edit with your actual API keys
```

### Step 5: Deploy

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop watching logs: Ctrl+C
```

### Step 6: Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","redis":"connected","version":"1.0.0"}
```

### Access Your Application

- **Frontend**: `http://YOUR_EC2_PUBLIC_IP:3000`
- **Backend API**: `http://YOUR_EC2_PUBLIC_IP:8000`
- **API Docs**: `http://YOUR_EC2_PUBLIC_IP:8000/docs`

### Optional: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/pdf-processor << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    client_max_body_size 25M;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/pdf-processor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Update .env with domain
sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://YOUR_DOMAIN|" .env

# Restart services
docker-compose down && docker-compose up -d
```

### Optional: Setup HTTPS with Let's Encrypt

```bash
# Only if you have a domain name
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Maintenance Commands

```bash
# View logs
docker-compose logs -f [service]  # backend, frontend, worker, redis

# Restart services
docker-compose restart

# Update to latest code
git pull origin main
docker-compose up -d --build

# Stop services
docker-compose down

# Remove all data (destructive!)
docker-compose down -v
```

---

## Option 2: Railway + Vercel (Git-Based Deployment)

### A. Deploy Backend on Railway

1. **Sign up at [railway.app](https://railway.app)**

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub
   - Select `alejochang/pdf-processor`

3. **Add Redis**
   - In your project, click "New"
   - Select "Database" → "Redis"
   - Railway will provide `REDIS_URL` automatically

4. **Configure Backend Service**
   - Click "New" → "GitHub Repo"
   - Select your repo
   - Click "Add variables" and set:
     ```
     REDIS_URL=${{Redis.REDIS_URL}}
     GOOGLE_API_KEY=your_gemini_key
     MISTRAL_API_KEY=your_mistral_key
     MAX_FILE_SIZE_MB=25
     ```
   - In Settings:
     - Root Directory: `backend`
     - Build Command: (leave empty, uses Dockerfile)
     - Start Command: (leave empty, uses Dockerfile CMD)

5. **Configure Worker Service**
   - Click "New" → "GitHub Repo"
   - Select your repo again
   - Add same environment variables as backend
   - In Settings:
     - Root Directory: `backend`
     - Start Command: `python -m app.worker`

6. **Deploy**
   - Railway auto-deploys on git push
   - Copy your backend URL (e.g., `https://your-app.railway.app`)

### B. Deploy Frontend on Vercel

1. **Sign up at [vercel.com](https://vercel.com)**

2. **Import Repository**
   - Click "New Project"
   - Import `alejochang/pdf-processor`

3. **Configure Project**
   - Framework Preset: Next.js
   - Root Directory: `frontend-nextjs`
   - Build Command: `npm run build`
   - Output Directory: `.next`

4. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-backend.railway.app
   ```

5. **Deploy**
   - Click "Deploy"
   - Vercel auto-deploys on git push to main

### C. Update Backend CORS

After deploying frontend, update backend CORS in `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-vercel-app.vercel.app"  # Add your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push - Railway will auto-redeploy.

---

## Option 3: Render (All-in-One)

### Prerequisites
- Sign up at [render.com](https://render.com)
- GitHub repository

### Step 1: Create Blueprint

Create `render.yaml` in your repo root:

```yaml
services:
  # Redis
  - type: redis
    name: pdf-processor-redis
    ipAllowList: []
    plan: free

  # Backend
  - type: web
    name: pdf-processor-backend
    env: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: pdf-processor-redis
          property: connectionString
      - key: GOOGLE_API_KEY
        value: YOUR_GEMINI_KEY
      - key: MISTRAL_API_KEY
        value: YOUR_MISTRAL_KEY
      - key: MAX_FILE_SIZE_MB
        value: 25

  # Worker
  - type: worker
    name: pdf-processor-worker
    env: docker
    dockerfilePath: ./backend/Dockerfile
    dockerCommand: python -m app.worker
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: pdf-processor-redis
          property: connectionString
      - key: GOOGLE_API_KEY
        value: YOUR_GEMINI_KEY
      - key: MISTRAL_API_KEY
        value: YOUR_MISTRAL_KEY

  # Frontend
  - type: web
    name: pdf-processor-frontend
    env: docker
    dockerfilePath: ./frontend-nextjs/Dockerfile
    envVars:
      - key: NEXT_PUBLIC_API_URL
        fromService:
          type: web
          name: pdf-processor-backend
          property: url
```

### Step 2: Deploy

1. Go to Render dashboard
2. Click "New" → "Blueprint"
3. Connect your GitHub repo
4. Select the repo
5. Render auto-deploys from `render.yaml`

---

## Option 4: AWS ECS (Production-Ready)

### Prerequisites
- AWS CLI installed and configured
- Docker installed locally

### Quick Deploy

```bash
# Make the script executable
chmod +x deploy-aws-ecs.sh

# Run deployment
./deploy-aws-ecs.sh
```

The script will:
1. Create ECR repositories
2. Build and push Docker images
3. Create ECS cluster
4. Register task definition
5. Set up CloudWatch logging

### Complete ECS Setup

After running the script, create the VPC and service:

```bash
# 1. Create VPC (if you don't have one)
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Get VPC ID from output, then create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# 2. Create security group
aws ec2 create-security-group \
    --group-name pdf-processor-sg \
    --description "PDF Processor Security Group" \
    --vpc-id vpc-xxx

# Allow inbound traffic
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 3000 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

# 3. Create ECS service
aws ecs create-service \
    --cluster pdf-processor-cluster \
    --service-name pdf-processor-service \
    --task-definition pdf-processor \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --region us-east-1
```

---

## 🔒 Security Best Practices

### 1. API Keys Management

**Never commit API keys to git!**

```bash
# Create .env.example template
cat > .env.example << EOF
REDIS_URL=redis://redis:6379
GOOGLE_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
MAX_FILE_SIZE_MB=25
UPLOAD_DIR=/app/uploads
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Add to .gitignore
echo ".env" >> .gitignore
```

**For production, use secrets management:**
- AWS: AWS Secrets Manager
- Railway: Built-in encrypted variables
- Vercel: Environment Variables (encrypted)
- Render: Environment Variables (encrypted)

### 2. HTTPS/SSL

**Always use HTTPS in production:**
- AWS: Use Application Load Balancer with ACM certificate
- EC2: Use Certbot + Let's Encrypt
- Railway/Vercel/Render: Free automatic HTTPS

### 3. Firewall Rules

**EC2 Security Groups:**
- Only allow port 22 from your IP (not 0.0.0.0/0)
- Use port 80/443 for public access
- Keep 3000/8000 closed if using reverse proxy

### 4. Update CORS

Update `backend/app/main.py` with your production domains:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring & Logging

### CloudWatch (AWS)

```bash
# View logs
aws logs tail /ecs/pdf-processor/backend --follow

# Create dashboard
aws cloudwatch put-dashboard \
    --dashboard-name pdf-processor \
    --dashboard-body file://cloudwatch-dashboard.json
```

### Docker Logs (EC2)

```bash
# Follow all services
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Monitoring Endpoints

Add to your monitoring service (e.g., Uptime Robot):
- `http://yourdomain.com/` (Frontend)
- `http://yourdomain.com/api/health` (Backend health)

---

## 💰 Cost Estimation

### AWS EC2 + Docker
- **t3.small**: ~$15/month
- **t3.medium**: ~$30/month
- **Storage (20GB)**: ~$2/month
- **Data Transfer**: ~$5-10/month
- **Total**: ~$20-45/month

### Railway + Vercel
- **Railway**: Free tier (500 hours/month) or $5/month
- **Vercel**: Free tier (100GB bandwidth)
- **Total**: $0-5/month (hobby), ~$20/month (production)

### AWS ECS
- **Fargate**: ~$30-50/month (1 task)
- **ALB**: ~$20/month (optional)
- **ECR**: ~$1/month
- **Total**: ~$30-70/month

### Render
- **Free tier**: $0 (with limitations)
- **Starter**: $7/service/month
- **Total**: $0-28/month

---

## 🚨 Troubleshooting

### Issue: Frontend can't connect to backend

**Solution:**
```bash
# Check NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_API_URL

# Should be your backend URL
# Update .env and rebuild
docker-compose up -d --build frontend
```

### Issue: Worker not processing jobs

**Solution:**
```bash
# Check worker logs
docker-compose logs worker

# Verify Redis connection
docker-compose exec backend redis-cli -h redis ping

# Restart worker
docker-compose restart worker
```

### Issue: Out of memory

**Solution:**
```bash
# Check memory usage
docker stats

# Increase EC2 instance size or
# Add swap memory:
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill process
kill -9 <PID>
```

---

## 🔄 CI/CD Setup

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ubuntu/pdf-processor
            git pull origin main
            docker-compose up -d --build
```

Add secrets in GitHub repo settings:
- `EC2_HOST`: Your EC2 public IP
- `EC2_SSH_KEY`: Contents of your `.pem` file

---

## 📝 Summary

**Easiest**: Railway + Vercel (click to deploy)
**Best for learning**: AWS EC2 + Docker
**Production-ready**: AWS ECS + ALB
**Budget-friendly**: Render free tier

Choose based on your needs, budget, and technical expertise!
