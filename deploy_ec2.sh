#!/bin/bash
# EC2 Deployment Script for Claude Code System

set -e  # Exit on error

echo "🚀 Claude Code EC2 Deployment Script"
echo "===================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS"
    exit 1
fi

# Function to install Python 3.11
install_python() {
    echo "📦 Installing Python 3.11..."
    if [ "$OS" = "ubuntu" ]; then
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
        sudo apt install -y python3.11 python3.11-venv python3.11-dev
    elif [ "$OS" = "amzn" ]; then
        sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel
        cd /tmp
        wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
        tar xzf Python-3.11.0.tgz
        cd Python-3.11.0
        ./configure --enable-optimizations
        make -j $(nproc)
        sudo make altinstall
        cd ~
    fi
}

# Function to install Node.js
install_nodejs() {
    echo "📦 Installing Node.js..."
    if [ "$OS" = "ubuntu" ]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt install -y nodejs
    elif [ "$OS" = "amzn" ]; then
        curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash -
        sudo yum install -y nodejs
    fi
}

# Function to install system dependencies
install_dependencies() {
    echo "📦 Installing system dependencies..."
    if [ "$OS" = "ubuntu" ]; then
        sudo apt install -y git nginx supervisor
    elif [ "$OS" = "amzn" ]; then
        sudo yum install -y git nginx
    fi
}

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    install_python
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    install_nodejs
fi

# Install system dependencies
install_dependencies

# Install Claude Code CLI
echo "📦 Installing Claude Code CLI..."
sudo npm install -g @anthropic-ai/claude-code

# Get EC2 metadata
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
EC2_PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)

echo "🌐 EC2 Public IP: $EC2_PUBLIC_IP"
echo "🔒 EC2 Private IP: $EC2_PRIVATE_IP"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment and install packages
echo "📦 Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn httpx aiohttp pydantic claude-code-sdk mcp

# Create .env file with EC2 configuration
echo "⚙️ Creating configuration..."
cat > .env << EOF
# EC2 Configuration
API_SERVER_URL=http://localhost:8001
PROJECT_ROOT=$PWD
EC2_PUBLIC_IP=$EC2_PUBLIC_IP
EC2_PRIVATE_IP=$EC2_PRIVATE_IP
EOF

# Update the webhook_frontend_unified.py to use EC2 IP
echo "🔧 Updating frontend configuration..."
sed -i "s/API_SERVER_URL = \"http:\/\/localhost:8001\"/API_SERVER_URL = os.environ.get('API_SERVER_URL', 'http:\/\/localhost:8001')/" webhook_frontend_unified.py

# Create systemd service files
echo "🔧 Creating systemd services..."

# API Server Service
sudo tee /etc/systemd/system/claude-api.service > /dev/null << EOF
[Unit]
Description=Claude Code API Server
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$PWD/.env
ExecStart=$PWD/venv/bin/python api_server_final.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend Server Service
sudo tee /etc/systemd/system/claude-frontend.service > /dev/null << EOF
[Unit]
Description=Claude Code Frontend Server
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$PWD/.env
ExecStart=$PWD/venv/bin/python webhook_frontend_unified.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🔧 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/claude-code > /dev/null << EOF
server {
    listen 80;
    server_name $EC2_PUBLIC_IP;

    # Frontend
    location / {
        proxy_pass http://localhost:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # API Proxy
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # SSE endpoint
    location /events {
        proxy_pass http://localhost:8002/events;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/claude-code /etc/nginx/sites-enabled/
sudo nginx -t

# Create directories
mkdir -p logs

# Reload systemd and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable claude-api claude-frontend nginx
sudo systemctl restart claude-api claude-frontend nginx

# Wait for services to start
sleep 5

# Check service status
echo "✅ Checking service status..."
sudo systemctl status claude-api --no-pager | head -10
sudo systemctl status claude-frontend --no-pager | head -10

# Test endpoints
echo "🧪 Testing endpoints..."
curl -s http://localhost:8001/health | jq . || echo "API health check failed"
curl -s http://localhost:8002/health | jq . || echo "Frontend health check failed"

echo "
✅ Deployment complete!

Access your Claude Code system at:
🌐 http://$EC2_PUBLIC_IP

To view logs:
📋 sudo journalctl -u claude-api -f
📋 sudo journalctl -u claude-frontend -f

To restart services:
🔄 sudo systemctl restart claude-api claude-frontend

Security reminder:
🔒 Make sure to configure your EC2 security groups to allow:
   - Port 80 (HTTP) from your IP addresses
   - Port 22 (SSH) from your IP address only
"