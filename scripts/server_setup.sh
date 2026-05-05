#!/bin/bash
# server_setup.sh — Run this once on a fresh Hetzner Ubuntu 24.04 server
# Usage: bash server_setup.sh
set -e

echo "══════════════════════════════════════════"
echo "  SenStat — Server Setup (Hetzner)"
echo "══════════════════════════════════════════"

# ── 1. System update ───────────────────────────────────────────────────────────
echo "▶ Updating system packages..."
apt-get update -q && apt-get upgrade -y -q

# ── 2. Install Docker ──────────────────────────────────────────────────────────
echo "▶ Installing Docker..."
apt-get install -y -q ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker

echo "✓ Docker $(docker --version) installed"

# ── 3. Install useful tools ────────────────────────────────────────────────────
echo "▶ Installing utilities..."
apt-get install -y -q git curl ufw htop

# ── 4. Configure firewall ──────────────────────────────────────────────────────
echo "▶ Configuring firewall..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "✓ Firewall configured (SSH + HTTP + HTTPS)"

# ── 5. Create app directory ────────────────────────────────────────────────────
mkdir -p /app
echo "✓ /app directory created"

# ── 6. Add swap (safety net for 8 GB RAM) ─────────────────────────────────────
if [ ! -f /swapfile ]; then
    echo "▶ Adding 4 GB swap..."
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "✓ 4 GB swap added"
fi

echo ""
echo "══════════════════════════════════════════"
echo "  Server setup complete!"
echo "══════════════════════════════════════════"
echo "  Next steps:"
echo "  1. cd /app"
echo "  2. git clone https://github.com/SenStat/Senstat-Agent.git ."
echo "  3. git checkout dev"
echo "  4. Upload data/chroma/ from your local machine"
echo "  5. cp .env.example .env && nano .env"
echo "  6. bash scripts/deploy.sh"
echo "══════════════════════════════════════════"
