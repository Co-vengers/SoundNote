#!/bin/bash
# SoundNote GCP VM Deployment Script
# Run this once on a fresh Ubuntu 22.04 VM
#
# Usage:
#   chmod +x deploy.sh
#   sudo ./deploy.sh

set -e

REPO_URL="https://github.com/Co-vengers/video_transcriber.git"
APP_DIR="/opt/soundnote"
SERVICE_NAME="soundnote"

echo "=== SoundNote Deployment Script ==="
echo ""

# ── 1. System update ──────────────────────────────────────────────────────────
echo "[1/7] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# ── 2. Install Docker ─────────────────────────────────────────────────────────
echo "[2/7] Installing Docker..."
if ! command -v docker &> /dev/null; then
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    echo "  Docker installed."
else
    echo "  Docker already installed, skipping."
fi

# ── 3. Clone repository ───────────────────────────────────────────────────────
echo "[3/7] Cloning repository to $APP_DIR..."
if [ -d "$APP_DIR" ]; then
    echo "  Directory exists - pulling latest changes..."
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# ── 4. Set up .env ────────────────────────────────────────────────────────────
echo "[4/7] Setting up environment configuration..."
if [ ! -f "$APP_DIR/video_transcriber/.env" ]; then
    cp "$APP_DIR/video_transcriber/.env.example" "$APP_DIR/video_transcriber/.env"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  ACTION REQUIRED: Edit the .env file before continuing      │"
    echo "  │                                                               │"
    echo "  │  nano $APP_DIR/video_transcriber/.env             │"
    echo "  │                                                               │"
    echo "  │  At minimum, set:                                            │"
    echo "  │    SECRET_KEY=<generate-a-strong-random-key>                 │"
    echo "  │    ALLOWED_HOSTS=localhost,127.0.0.1,<YOUR_VM_EXTERNAL_IP>   │"
    echo "  │    DEBUG=False                                               │"
    echo "  │    DB_PASSWORD=<strong-password>                             │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  Press Enter after you have saved the .env file..."
    read -r
else
    echo "  .env already exists, skipping."
fi

# ── 5. Install systemd service ────────────────────────────────────────────────
echo "[5/7] Installing systemd service..."
cp "$APP_DIR/soundnote.service" /etc/systemd/system/${SERVICE_NAME}.service
# Update WorkingDirectory to match app dir
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$APP_DIR|g" \
    /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
echo "  systemd service installed and enabled."

# ── 6. Build and start ────────────────────────────────────────────────────────
echo "[6/7] Building Docker images and starting services..."
cd "$APP_DIR"
docker compose build --quiet
systemctl start ${SERVICE_NAME}.service
echo "  Services started."

# ── 7. Verify ─────────────────────────────────────────────────────────────────
echo "[7/7] Verifying deployment..."
sleep 10  # Allow services to initialize
if systemctl is-active --quiet ${SERVICE_NAME}.service; then
    echo ""
    echo "  ✅ SoundNote is running!"
    echo ""
    EXTERNAL_IP=$(curl -sf "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" \
        -H "Metadata-Flavor: Google" 2>/dev/null || echo "<your-vm-external-ip>")
    echo "  Access the application at: http://$EXTERNAL_IP:8000"
    echo ""
    echo "  Useful commands:"
    echo "    View logs:     sudo journalctl -u soundnote -f"
    echo "    View web logs: docker compose logs -f web"
    echo "    Restart:       sudo systemctl restart soundnote"
    echo "    Stop:          sudo systemctl stop soundnote"
    echo "    Status:        sudo systemctl status soundnote"
    echo ""
    echo "  Create admin user:"
    echo "    cd $APP_DIR && docker compose exec -T web python manage.py createsuperuser"
else
    echo ""
    echo "  ❌ Service failed to start. Check logs:"
    echo "    sudo journalctl -u soundnote -n 50"
    echo "    docker compose logs"
    exit 1
fi
