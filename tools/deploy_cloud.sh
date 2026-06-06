#!/bin/bash
# Deploy the T-RGB bot cloud server to Tencent Cloud (or any Linux server).
#
# Prerequisites:
#   1. A Tencent Cloud CVM instance (or any Linux VPS) running Ubuntu 22.04+
#   2. Python 3.10+ installed
#   3. Your DEEPSEEK_API_KEY set in /etc/environment or a .env file
#
# Usage on the server:
#   scp -r tools/ user@your-server-ip:~/xiaoyuan/
#   ssh user@your-server-ip
#   cd ~/xiaoyuan/tools && bash deploy_cloud.sh

set -e

APP_DIR="/opt/xiaoyuan"
SERVICE_NAME="xiaoyuan-bot"
VENV_DIR="$APP_DIR/.venv"
PORT=8080

echo "=== Installing system dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip nginx

echo "=== Creating app directory ==="
sudo mkdir -p "$APP_DIR"
sudo cp -r . "$APP_DIR/tools"
sudo chown -R $USER:$USER "$APP_DIR"

echo "=== Setting up Python venv ==="
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install -q flask
deactivate

echo "=== Creating systemd service ==="
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=XiaoYuan Bot Cloud Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR/tools
Environment="DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-YOUR_KEY_HERE}"
Environment="BOT_URL=http://YOUR_T-RGB_IP"
Environment="BOT_CONFIG=$APP_DIR/tools/bot_configs/default.json"
Environment="DEEPSEEK_MODEL=deepseek-v4-flash"
ExecStart=$VENV_DIR/bin/python3 $APP_DIR/tools/cloud_server.py --port $PORT --host 127.0.0.1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "=== Setting up Nginx reverse proxy ==="
sudo tee /etc/nginx/sites-available/$SERVICE_NAME > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "=== Starting service ==="
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo ""
echo "=== Deploy complete! ==="
echo "Check status:  sudo systemctl status $SERVICE_NAME"
echo "View logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "Test:          curl http://YOUR_SERVER_IP/health"
echo ""
echo "IMPORTANT: Edit /etc/systemd/system/$SERVICE_NAME.service"
echo "  - Replace YOUR_KEY_HERE with your actual DeepSeek API key"
echo "  - Replace YOUR_T-RGB_IP with the T-RGB's local IP"
echo "Then: sudo systemctl daemon-reload && sudo systemctl restart $SERVICE_NAME"
