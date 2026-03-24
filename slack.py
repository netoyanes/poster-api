"""
slack.py — Uploads poster + banner PNGs to Slack and posts a feedback message.
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

    headers = {"Authorization": f"Bearer {token}"}

    # Upload poster
    poster_url = _upload_file(
        token=token,
        path=poster_path,
        filename="poster.png",
        title=f"{title} — Poster",
        channel=channel,
    )

    # Upload banner
    banner_url = _upload_file(
        token=token,
        path=banner_path,
        filename="banner.png",
        title=f"{title} — Banner",
        channel=channel,
    )

    # Post a message with context + emoji reactions prompt
    message = (
        f":frame_with_picture: *New design ready for review*\n"
        f">*{title}*\n"
        f">{date}  ·  {time}\n\n"
        f"React with :white_check_mark: to approve or :pencil: to request changes.\n"
        f"_Airtable record: `{record_id}`_"
    )

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=headers,
        json={"channel": channel, "text": message},
    )
    resp.raise_for_status()
    result = resp.json()

    return {
        "ok": result.get("ok"),
        "ts": result.get("ts"),
        "poster_uploaded": poster_url,
        "banner_uploaded": banner_url,
    }


def _upload_file(token: str, path: str, filename: str, title: str, channel: str) -> bool:
    """Upload a file to Slack using the files.uploadV2 API."""
    with open(path, "rb") as f:
        resp = requests.post(
            "https://slack.com/api/files.upload",
            headers={"Authorization": f"Bearer {token}"},
            data={"channels": channel, "filename": filename, "title": title},
            files={"file": (filename, f, "image/png")},
        )
    resp.raise_for_status()
    data = resp.json()
    return data.get("ok", False)
