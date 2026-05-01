#!/bin/bash
# deploy.sh — First-time deployment script for SenStat
set -e

echo "══════════════════════════════════════════"
echo "  SenStat — Deployment Script"
echo "══════════════════════════════════════════"

# ── 1. Check .env ──────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example and fill in your API key."
    exit 1
fi

if ! grep -q "ANTHROPIC_API_KEY=sk-" .env; then
    echo "❌ ANTHROPIC_API_KEY missing or invalid in .env"
    exit 1
fi

echo "✓ .env found"

# ── 2. Check ChromaDB ──────────────────────────────────────────────────────────
if [ ! -f "data/chroma/chroma.sqlite3" ]; then
    echo ""
    echo "⚠️  data/chroma/ is empty."
    echo "   Option A: copy the chroma/ folder from your local machine:"
    echo "     scp -r ./data/chroma user@server:/app/data/"
    echo "   Option B: run ingestion after placing PDFs in data/raw/:"
    echo "     docker compose run --rm api python -m ingestion.pipeline"
    echo ""
    read -p "Continue anyway? (y/N) " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        exit 0
    fi
fi

# ── 3. Build images ────────────────────────────────────────────────────────────
echo ""
echo "▶ Building Docker images (first build ~5 min)..."
docker compose build

# ── 4. Start services ──────────────────────────────────────────────────────────
echo ""
echo "▶ Starting services..."
echo "  Note: API takes ~60s on first start (embedding model download ~2.1 GB)"
docker compose up -d

# ── 5. Wait for API health ─────────────────────────────────────────────────────
echo ""
echo "▶ Waiting for API to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ API is healthy"
        break
    fi
    echo "  ... waiting ($i/30)"
    sleep 10
done

# ── 6. Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo "  SenStat is running!"
echo "══════════════════════════════════════════"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
echo "  Grand Public  →  http://$SERVER_IP"
echo "  Interface Pro →  http://$SERVER_IP/pro"
echo "  API REST      →  http://$SERVER_IP/api/health"
echo ""
echo "  Logs: docker compose logs -f api"
echo "══════════════════════════════════════════"
