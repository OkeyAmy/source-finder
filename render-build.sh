#!/usr/bin/env bash
# Script to install Playwright dependencies for Render deployment

echo "📦 Installing system dependencies for Playwright..."
apt-get update
apt-get install -y libgtk-3-0 libdbus-glib-1-2 libxt6 libxaw7 libnss3 libnspr4 libpcre3 libasound2 libxdamage1 libgbm1 libxfixes3

echo "🌐 Installing Playwright browsers..."
python -m playwright install chromium

echo "✅ Playwright dependencies installed successfully" 