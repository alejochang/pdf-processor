#!/bin/bash

# Simple EC2 Deployment Script for PDF Processor
# Run this script on a fresh Ubuntu 22.04 EC2 instance

set -e

echo "=== PDF Processor EC2 Deployment Script ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Update system
echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# Step 2: Install Docker
echo ""
echo "Step 2: Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt install -y docker.io docker-compose git
    sudo usermod -aG docker $USER
    print_success "Docker installed"
else
    print_warning "Docker already installed"
fi

# Step 3: Clone repository
echo ""
echo "Step 3: Cloning repository..."
if [ ! -d "pdf-processor" ]; then
    git clone https://github.com/alejochang/pdf-processor.git
    cd pdf-processor
    print_success "Repository cloned"
else
    cd pdf-processor
    git pull origin main
    print_success "Repository updated"
fi

# Step 4: Get public IP
echo ""
echo "Step 4: Detecting public IP..."
if command -v curl &> /dev/null; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    print_success "Public IP: $PUBLIC_IP"
else
    PUBLIC_IP="localhost"
    print_warning "Could not detect public IP, using localhost"
fi

# Step 5: Configure environment
echo ""
echo "Step 5: Configuring environment..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
REDIS_URL=redis://redis:6379
GOOGLE_API_KEY=REPLACE_WITH_YOUR_GEMINI_KEY
MISTRAL_API_KEY=REPLACE_WITH_YOUR_MISTRAL_KEY
MAX_FILE_SIZE_MB=25
UPLOAD_DIR=/app/uploads
NEXT_PUBLIC_API_URL=http://$PUBLIC_IP:8000
EOF
    print_success ".env file created"
    print_warning "IMPORTANT: Edit .env file and add your API keys!"
    echo ""
    echo "Run: nano .env"
    echo "Replace REPLACE_WITH_YOUR_GEMINI_KEY with your actual Gemini API key"
    echo "Replace REPLACE_WITH_YOUR_MISTRAL_KEY with your actual Mistral API key"
    echo ""
    read -p "Press Enter after editing .env file..." dummy
else
    print_warning ".env file already exists, skipping creation"
fi

# Step 6: Start services
echo ""
echo "Step 6: Starting Docker services..."
newgrp docker << END
docker-compose up -d --build
END

print_success "Services starting..."

# Step 7: Wait for services to be ready
echo ""
echo "Step 7: Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    print_success "Services are running!"
else
    print_error "Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Step 8: Verify deployment
echo ""
echo "Step 8: Verifying deployment..."

# Check backend health
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_success "Backend is healthy"
else
    print_warning "Backend health check failed"
fi

# Step 9: Display access information
echo ""
echo "================================================================"
echo "                 DEPLOYMENT COMPLETE!                            "
echo "================================================================"
echo ""
echo "🌐 Access your application:"
echo ""
if [ "$PUBLIC_IP" != "localhost" ]; then
    echo "   Frontend:    http://$PUBLIC_IP:3000"
    echo "   Backend API: http://$PUBLIC_IP:8000"
    echo "   API Docs:    http://$PUBLIC_IP:8000/docs"
else
    echo "   Frontend:    http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs:    http://localhost:8000/docs"
fi
echo ""
echo "================================================================"
echo ""
echo "📋 Useful commands:"
echo ""
echo "   View logs:           docker-compose logs -f"
echo "   View status:         docker-compose ps"
echo "   Restart services:    docker-compose restart"
echo "   Stop services:       docker-compose down"
echo "   Update code:         git pull && docker-compose up -d --build"
echo ""
echo "================================================================"
echo ""
echo "🔒 Security reminders:"
echo ""
echo "   1. Make sure your API keys are set in .env"
echo "   2. Configure EC2 security group to restrict SSH (port 22) to your IP"
echo "   3. Consider setting up HTTPS with Nginx + Let's Encrypt"
echo "   4. Regular updates: apt update && apt upgrade"
echo ""
echo "================================================================"
echo ""
echo "📚 Full documentation: DEPLOYMENT_GUIDE.md"
echo ""

# Optional: Install Nginx
echo ""
read -p "Would you like to install Nginx reverse proxy? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing Nginx..."
    sudo apt install -y nginx

    # Create Nginx config
    sudo tee /etc/nginx/sites-available/pdf-processor << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 25M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://localhost:8000;
    }
}
NGINX_EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/pdf-processor /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl restart nginx

    print_success "Nginx installed and configured"
    echo ""
    echo "You can now access the application at: http://$PUBLIC_IP (port 80)"
    echo ""

    # Update .env
    if [ "$PUBLIC_IP" != "localhost" ]; then
        sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=http://$PUBLIC_IP|" .env
        docker-compose down && docker-compose up -d
        print_success ".env updated with Nginx configuration"
    fi
fi

echo ""
echo "✅ Setup complete! Enjoy your PDF Processor application!"
