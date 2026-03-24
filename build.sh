#!/usr/bin/env bash
# build.sh — run by Render during deployment
set -e

pip install -r requirements.txt
python -m playwright install --with-deps chromium
