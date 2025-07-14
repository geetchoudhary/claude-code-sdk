# EC2 Setup Guide for Claude Code with Approval System

## Prerequisites
- EC2 instance with Ubuntu 20.04+ or Amazon Linux 2
- SSH access to your EC2 instance
- Security groups configured for ports 8001, 8002 (and optionally 8083)

## Step 1: Connect to EC2 and Update System

```bash
ssh -i your-key.pem ec2-user@your-ec2-ip
# or for Ubuntu:
# ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y  # For Ubuntu
# or
sudo yum update -y  # For Amazon Linux
```

## Step 2: Install Python 3.11+ and Dependencies

### For Ubuntu:
```bash
# Install Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install git and other tools
sudo apt install git nginx supervisor -y
```

### For Amazon Linux 2:
```bash
# Install Python 3.11
sudo yum install gcc openssl-devel bzip2-devel libffi-devel -y
cd /tmp
wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz
tar xzf Python-3.11.0.tgz
cd Python-3.11.0
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall

# Install git and other tools
sudo yum install git nginx -y
```

## Step 3: Install Node.js and Claude Code CLI

```bash
# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs  # Ubuntu
# or
curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install nodejs -y  # Amazon Linux

# Install Claude Code CLI
sudo npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version
```

## Step 4: Clone Your Repository

```bash
cd ~
git clone https://github.com/yourusername/claude_test.git
cd claude_test
```

## Step 5: Create Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install fastapi uvicorn httpx aiohttp pydantic claude-code-sdk
pip install mcp  # If you have MCP server dependencies
```

## Step 6: Configure Security Groups

In AWS Console, configure your EC2 security group to allow:
- Port 22 (SSH) - from your IP
- Port 8001 (API Server) - from anywhere or specific IPs
- Port 8002 (Frontend) - from anywhere (for web access)
- Port 8083 (MCP Callback) - only from localhost (not needed externally)

## Step 7: Create Systemd Services

Create service files to run your servers automatically:

### API Server Service
```bash
sudo nano /etc/systemd/system/claude-api.service
```

Add:
```ini
[Unit]
Description=Claude Code API Server
After=network.target

[Service]
Type=exec
User=ubuntu
WorkingDirectory=/home/ubuntu/claude_test
Environment="PATH=/home/ubuntu/claude_test/venv/bin"
ExecStart=/home/ubuntu/claude_test/venv/bin/python api_server_final.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Frontend Server Service
```bash
sudo nano /etc/systemd/system/claude-frontend.service
```

Add:
```ini
[Unit]
Description=Claude Code Frontend Server
After=network.target

[Service]
Type=exec
User=ubuntu
WorkingDirectory=/home/ubuntu/claude_test
Environment="PATH=/home/ubuntu/claude_test/venv/bin"
ExecStart=/home/ubuntu/claude_test/venv/bin/python webhook_frontend_unified.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Step 8: Configure Environment

Create a `.env` file for your EC2 configuration:
```bash
nano ~/claude_test/.env
```

Add:
```bash
# EC2 Configuration
API_SERVER_URL=http://localhost:8001
PROJECT_ROOT=/home/ubuntu/claude_test
CLAUDE_API_KEY=your-claude-api-key  # If needed
```

## Step 9: Update Frontend for EC2

Modify the frontend to work with EC2's public IP:

```bash
# Get your EC2 public IP
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Your EC2 public IP: $EC2_PUBLIC_IP"

# Update the webhook_frontend_unified.py to use environment variable
```

## Step 10: Configure Nginx (Optional but Recommended)

```bash
sudo nano /etc/nginx/sites-available/claude-code
```

Add:
```nginx
server {
    listen 80;
    server_name your-ec2-ip;

    location / {
        proxy_pass http://localhost:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/claude-code /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 11: Start Services

```bash
# Enable and start services
sudo systemctl enable claude-api
sudo systemctl enable claude-frontend
sudo systemctl start claude-api
sudo systemctl start claude-frontend

# Check status
sudo systemctl status claude-api
sudo systemctl status claude-frontend

# View logs
sudo journalctl -u claude-api -f
sudo journalctl -u claude-frontend -f
```

## Step 12: Configure Claude Code CLI

On the EC2 instance, configure Claude Code:
```bash
# Set up Claude Code configuration
mkdir -p ~/.claude
nano ~/.claude/settings.json
```

Add your configuration for MCP servers and other settings.

## Step 13: Test the Setup

1. Access your frontend at: `http://your-ec2-ip:8002` (or port 80 if using Nginx)
2. Test creating a new session
3. Test approval functionality

## Step 14: SSL/HTTPS Setup (Optional)

For production use, set up SSL using Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Troubleshooting

1. **Check service logs:**
   ```bash
   sudo journalctl -u claude-api -n 50
   sudo journalctl -u claude-frontend -n 50
   ```

2. **Check ports are listening:**
   ```bash
   sudo netstat -tlnp | grep -E '8001|8002'
   ```

3. **Test API locally:**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   ```

4. **Common issues:**
   - Firewall blocking ports: Check security groups
   - Python path issues: Verify virtual environment activation
   - Permission issues: Check file ownership

## Security Considerations

1. **API Keys**: Store sensitive keys in environment variables or AWS Secrets Manager
2. **Access Control**: Restrict API access using security groups or API keys
3. **Updates**: Keep system and dependencies updated
4. **Monitoring**: Set up CloudWatch or similar monitoring

## Maintenance

### Update code:
```bash
cd ~/claude_test
git pull
sudo systemctl restart claude-api claude-frontend
```

### View logs:
```bash
tail -f ~/claude_test/permission_decisions.log
```

### Backup:
```bash
# Create backup script
tar -czf claude-backup-$(date +%Y%m%d).tar.gz ~/claude_test
```