"""
renderer.py — Builds HTML from event data and screenshots it to PNG via Playwright.
"""

import os
import tempfile
from playwright.sync_api import sync_playwright

# ── HTML Templates ────────────────────────────────────────────────────────────

POSTER_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ width:1080px; height:1440px; overflow:hidden; }}
    .poster {{
      width:1080px; height:1440px;
      position:relative;
      background: url({image_url}) lightgray 50% / cover no-repeat;
      font-family:'Figtree',sans-serif;
      overflow:hidden;
    }}
    .overlay {{
      position:absolute; inset:0;
      background: linear-gradient(to top, rgba(0,0,0,0.55) 0%, transparent 55%);
    }}
    .content {{
      position:absolute;
      bottom:284px; left:85px; right:84px;
      color:white;
    }}
    .logo {{ width:48px; height:48px; margin-bottom:28px; }}
    h1 {{
      font-size:{h1_size}px; font-weight:800;
      line-height:0.95; margin:0 0 20px;
      letter-spacing:-1.5px;
    }}
    .date {{ font-size:30px; font-weight:600; margin:0 0 28px; }}
    .time {{ font-size:30px; font-weight:400; }}
  </style>
</head>
<body>
  <div class="poster">
    <div class="overlay"></div>
    <div class="content">
      <svg class="logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M24 3 C24 3 21 17 17 21 C13 25 3 24 3 24 C3 24 13 23 17 27 C21 31 24 45 24 45 C24 45 27 31 31 27 C35 23 45 24 45 24 C45 24 35 25 31 21 C27 17 24 3 24 3Z" fill="white"/>
      </svg>
      <h1>{title}</h1>
      <p class="date">{date}</p>
      <p class="time">{time}</p>
    </div>
  </div>
</body>
</html>"""

BANNER_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ width:1024px; height:274px; overflow:hidden; }}
    .banner {{
      width:1024px; height:274px;
      position:relative;
      background: url({image_url}) lightgray 50% / cover no-repeat;
      font-family:'Figtree',sans-serif;
      overflow:hidden;
    }}
    .overlay {{
      position:absolute; inset:0;
      background: linear-gradient(to right, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.15) 60%, transparent 100%);
    }}
    .content {{
      position:absolute; inset:0;
      display:flex; align-items:flex-end;
      justify-content:space-between;
      padding:0 48px 32px;
      color:white;
    }}
    .left {{ display:flex; flex-direction:column; gap:6px; }}
    .logo {{ width:36px; height:36px; margin-bottom:4px; }}
    h1 {{ font-size:52px; font-weight:800; line-height:0.95; letter-spacing:-1px; }}
    .date {{ font-size:22px; font-weight:600; }}
    .time {{ font-size:32px; font-weight:400; align-self:flex-end; padding-bottom:4px; }}
  </style>
</head>
<body>
  <div class="banner">
    <div class="overlay"></div>
    <div class="content">
      <div class="left">
        <svg class="logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M24 3 C24 3 21 17 17 21 C13 25 3 24 3 24 C3 24 13 23 17 27 C21 31 24 45 24 45 C24 45 27 31 31 27 C35 23 45 24 45 24 C45 24 35 25 31 21 C27 17 24 3 24 3Z" fill="white"/>
        </svg>
        <h1>{title}</h1>
        <p class="date">{date}</p>
      </div>
      <p class="time">{time}</p>
    </div>
  </div>
</body>
</html>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _h1_size(title: str) -> int:
    """Reduce font size for long titles to avoid overflow."""
    if len(title) > 25:
        return 72
    if len(title) > 20:
        return 80
    return 96


def _screenshot(html: str, output_path: str, width: int, height: int):
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"file://{os.path.abspath(tmp_path)}")
            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(
                path=output_path,
                clip={"x": 0, "y": 0, "width": width, "height": height}
            )
            browser.close()
    finally:
        os.unlink(tmp_path)


# ── Public API ────────────────────────────────────────────────────────────────

def render_poster(title: str, date: str, time: str, image_url: str, output_path: str):
    html = POSTER_HTML.format(
        title=title, date=date, time=time,
        image_url=image_url, h1_size=_h1_size(title)
    )
    _screenshot(html, output_path, 1080, 1440)


def render_banner(title: str, date: str, time: str, image_url: str, output_path: str):
    html = BANNER_HTML.format(
        title=title, date=date, time=time, image_url=image_url
    )
    _screenshot(html, output_path, 1024, 274)
