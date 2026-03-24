"""
slack.py — Uploads poster + banner PNGs to Slack and posts a feedback message.

Uses the current Slack file upload V2 flow:
  1. files.getUploadURLExternal  → get upload URL + file_id
  2. PUT file bytes to upload URL
  3. files.completeUploadExternal → finalize and share to channel
"""

import os
import requests


def post_to_slack(
    channel: str,
    token: str,
    title: str,
    date: str,
    time: str,
    record_id: str,
    poster_path: str,
    banner_path: str,
) -> dict:
    """Upload both images and send a feedback request message."""

    # Upload poster + banner using V2 flow
    poster_ok = _upload_file_v2(
        token=token,
        path=poster_path,
        filename="poster.png",
        title=f"{title} — Poster",
        channel=channel,
    )

    banner_ok = _upload_file_v2(
        token=token,
        path=banner_path,
        filename="banner.png",
        title=f"{title} — Banner",
        channel=channel,
    )

    # Post a context + review prompt message
    message = (
        f":frame_with_picture: *New design ready for review*\n"
        f">*{title}*\n"
        f">{date}  ·  {time}\n\n"
        f"React with :white_check_mark: to approve or :pencil: to request changes.\n"
        f"_Airtable record: `{record_id}`_"
    )

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "text": message},
    )
    resp.raise_for_status()
    result = resp.json()

    return {
        "ok": result.get("ok"),
        "ts": result.get("ts"),
        "poster_uploaded": poster_ok,
        "banner_uploaded": banner_ok,
    }


def _upload_file_v2(token: str, path: str, filename: str, title: str, channel: str) -> bool:
    """
    Upload a file using Slack's V2 API (files.getUploadURLExternal flow).

    Step 1 — request an upload URL from Slack.
    Step 2 — PUT the raw file bytes directly to that URL (no auth header).
    Step 3 — call completeUploadExternal to attach the file to a channel.
    """
    headers = {"Authorization": f"Bearer {token}"}
    file_size = os.path.getsize(path)

    # ── Step 1: get upload URL ────────────────────────────────────────────────
    resp = requests.get(
        "https://slack.com/api/files.getUploadURLExternal",
        headers=headers,
        params={"filename": filename, "length": file_size},
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"Slack getUploadURLExternal failed: {data.get('error')}")

    upload_url = data["upload_url"]
    file_id    = data["file_id"]

    # ── Step 2: PUT file bytes to the upload URL ──────────────────────────────
    with open(path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": "image/png"},
        )
    put_resp.raise_for_status()

    # ── Step 3: complete the upload and share to channel ─────────────────────
    complete_resp = requests.post(
        "https://slack.com/api/files.completeUploadExternal",
        headers=headers,
        json={
            "files": [{"id": file_id, "title": title}],
            "channel_id": channel,
        },
    )
    complete_resp.raise_for_status()
    result = complete_resp.json()

    if not result.get("ok"):
        raise RuntimeError(f"Slack completeUploadExternal failed: {result.get('error')}")

    return True
