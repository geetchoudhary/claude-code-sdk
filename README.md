# Claude Code with Approval System

A web-based interface for interacting with Claude AI that includes real-time permission approvals.

## Quick Start

### Local Development
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run servers
python api_server_final.py          # Terminal 1
python webhook_frontend_unified.py  # Terminal 2

# Access at http://localhost:8002
```

### Production Deployment (Ubuntu 24.04)
```bash
# Clone and setup
git clone <your-repo>
cd claude_test
./setup_ubuntu_24.sh

# Access at http://your-server-ip
```

## Architecture

- **API Server** (Port 8001): Handles Claude AI queries
- **Frontend Server** (Port 8002): Web UI and approval handling  
- **Nginx** (Port 80): Reverse proxy for production

## Configuration

1. Edit `mcp-servers.json` for MCP server settings
2. Create `.env` file for environment variables:
   ```
   API_SERVER_URL=http://localhost:8001
   PROJECT_ROOT=/path/to/project
   ```

## Monitoring

```bash
# View logs
sudo journalctl -u claude-api -f
sudo journalctl -u claude-frontend -f

# Check status
sudo systemctl status claude-api
sudo systemctl status claude-frontend
```

## Security

- Configure EC2 security groups to allow only ports 22 and 80
- Use SSL/HTTPS in production (see EC2_SETUP.md)
- Store sensitive keys in environment variables

See [EC2_SETUP.md](EC2_SETUP.md) for detailed deployment instructions.