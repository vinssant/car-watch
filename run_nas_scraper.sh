#!/bin/bash
# =============================================================
# run_nas_scraper.sh — Scraper NAS (IP résidentielle)
# Lance les scrapers bloqués sur GitHub Actions
# Cron Synology : 7h30 quotidien
# =============================================================

PROJECT_DIR="/var/services/homes/vinssant/car-watch"
LOG_FILE="$PROJECT_DIR/logs/nas_scraper.log"
RESULTS_FILE="$PROJECT_DIR/data/nas_results.json"

mkdir -p "$PROJECT_DIR/logs"

echo "========================================" >> "$LOG_FILE"
echo "🚗 NAS Scraper démarré : $(date '+%d/%m/%Y %H:%M:%S')" >> "$LOG_FILE"

# Lancer le scraper NAS via Docker
docker run --rm \
  --network host \
  --name car-watch-nas-$(date +%s) \
  -v "$PROJECT_DIR:/app" \
  -e NAS_MODE=true \
  -e GMAIL_TOKEN="$(cat $PROJECT_DIR/.gmail_token 2>/dev/null || echo '')" \
  python:3.11-slim \
  bash -c "
    cd /app &&
    pip install httpx beautifulsoup4 lxml google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dateutil -q &&
    python3 main.py --scrapers-nas
  " >> "$LOG_FILE" 2>&1

echo "✅ NAS Scraper terminé : $(date '+%d/%m/%Y %H:%M:%S')" >> "$LOG_FILE"
