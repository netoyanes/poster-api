"""
Event Poster API
Receives a webhook from Airtable (via Make.com), generates poster + banner PNGs,
and posts them to Slack for feedback.
"""

import os
import tempfile
import requests
from flask import Flask, request, jsonify
from renderer import render_poster, render_banner
from slack import post_to_slack

app = Flask(__name__)

# --- Config (set these as environment variables on Render) ---
API_SECRET = os.environ.get("API_SECRET", "change-me")   # Simple token auth
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#design-feedback")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/generate", methods=["POST"])
def generate():
    # --- Auth ---
    token = request.headers.get("X-API-Secret", "")
    if token != API_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # --- Parse body ---
    data = request.get_json(force=True)
    required = ["title", "date", "time", "image_url", "record_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    title     = data["title"]
    date      = data["date"]       # e.g. "miércoles, 24 marzo"
    time      = data["time"]       # e.g. "6:00 pm"
    image_url = data["image_url"]  # Airtable attachment URL
    record_id = data["record_id"]  # For Slack message context

    # --- Render PNGs ---
    with tempfile.TemporaryDirectory() as tmpdir:
        poster_path = os.path.join(tmpdir, "poster.png")
        banner_path = os.path.join(tmpdir, "banner.png")

        render_poster(title, date, time, image_url, poster_path)
        render_banner(title, date, time, image_url, banner_path)

        # --- Post to Slack ---
        slack_result = post_to_slack(
            channel=SLACK_CHANNEL,
            token=SLACK_BOT_TOKEN,
            title=title,
            date=date,
            time=time,
            record_id=record_id,
            poster_path=poster_path,
            banner_path=banner_path,
        )

    return jsonify({"status": "posted", "slack": slack_result})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
