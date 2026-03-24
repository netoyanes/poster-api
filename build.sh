#!/usr/bin/env bash
# build.sh — run by Render during deployment
set -e

pip install -r requirements.txt

# Install Chromium system dependencies directly (Render builds run as root)
apt-get update -y && apt-get install -y --no-install-recommends \
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libdbus-1-3 \
  libxcb1 \
  libxkbcommon0 \
  libx11-6 \
  libxcomposite1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libpango-1.0-0 \
  libcairo2 \
  libasound2

# Install browser only — system deps already handled above
python -m playwright install chromium
