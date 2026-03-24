"""
renderer.py — Builds HTML from event data and screenshots it to PNG via Playwright.

Design matches Figma Pod-MX node 1943-2:
  - Dela Gothic One for title + date (display weight, tight tracking)
  - Urbanist Bold for time (lowercase, drop shadow)
  - Logo + text anchored mid-frame (~590px from top)
  - Time sits as a separate absolute block at 1078px
"""

import os
import tempfile
from playwright.sync_api import sync_playwright


# ── HTML Templates ────────────────────────────────────────────────────────────

POSTER_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <link href="https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Urbanist:wght@700&display=swap" rel="stylesheet">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ width:1080px; height:1440px; overflow:hidden; background:#111; }}
    .poster {{
      width:1080px; height:1440px;
      position:relative;
      overflow:hidden;
    }}
    .bg {{
      position:absolute; inset:0;
      background: url({image_url}) lightgray 50% / cover no-repeat;
    }}
    /* Subtle overlay so text stays legible on bright images */
    .overlay {{
      position:absolute; inset:0;
      background: linear-gradient(to top,
        rgba(0,0,0,0.55) 0%,
        rgba(0,0,0,0.25) 45%,
        transparent 65%);
    }}
    /* 4-point star logo — sits directly above the title */
    .logo {{
      position:absolute;
      top:590px;
      left:85px;
      width:72px;
      height:72px;
    }}
    /* Title + date block starts just below the logo */
    .text-block {{
      position:absolute;
      top:672px;
      left:85px;
      right:84px;
      color:white;
      font-family:'Dela Gothic One', sans-serif;
      font-weight:400;
    }}
    h1 {{
      font-size:{h1_size}px;
      line-height:1.1;
      letter-spacing:-1.8px;
      margin:0 0 10px;
    }}
    .date {{
      font-size:50px;
      line-height:1.33;
      letter-spacing:-1.8px;
      margin:0;
    }}
    /* Time sits as its own block, separate from the title area */
    .time {{
      position:absolute;
      top:1078px;
      left:85px;
      right:84px;
      font-family:'Urbanist', sans-serif;
      font-weight:700;
      font-size:60px;
      line-height:1.1;
      letter-spacing:-1.2px;
      text-transform:lowercase;
      text-shadow:0px 4px 4px rgba(0,0,0,0.36);
      color:white;
    }}
  </style>
</head>
<body>
  <div class="poster">
    <div class="bg"></div>
    <div class="overlay"></div>
    <svg class="logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M24 3 C24 3 21 17 17 21 C13 25 3 24 3 24 C3 24 13 23 17 27 C21 31 24 45 24 45 C24 45 27 31 31 27 C35 23 45 24 45 24 C45 24 35 25 31 21 C27 17 24 3 24 3Z" fill="white"/>
    </svg>
    <div class="text-block">
      <h1>{title}</h1>
      <p class="date">{date}</p>
    </div>
    <p class="time">{time}</p>
  </div>
</body>
</html>"""


BANNER_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <link href="https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Urbanist:wght@700&display=swap" rel="stylesheet">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ width:1024px; height:274px; overflow:hidden; background:#111; }}
    .banner {{
      width:1024px; height:274px;
      position:relative;
      overflow:hidden;
    }}
    .bg {{
      position:absolute; inset:0;
      background: url({image_url}) lightgray 50% / cover no-repeat;
    }}
    .overlay {{
      position:absolute; inset:0;
      background: linear-gradient(to right,
        rgba(0,0,0,0.60) 0%,
        rgba(0,0,0,0.25) 55%,
        transparent 100%);
    }}
    .content {{
      position:absolute; inset:0;
      display:flex;
      align-items:flex-end;
      justify-content:space-between;
      padding:0 48px 28px;
      color:white;
    }}
    .left {{
      display:flex;
      flex-direction:column;
      gap:4px;
    }}
    .logo {{
      width:36px;
      height:36px;
      margin-bottom:6px;
    }}
    h1 {{
      font-family:'Dela Gothic One', sans-serif;
      font-weight:400;
      font-size:52px;
      line-height:1.0;
      letter-spacing:-1.5px;
    }}
    .date {{
      font-family:'Dela Gothic One', sans-serif;
      font-weight:400;
      font-size:22px;
      line-height:1.2;
      letter-spacing:-0.8px;
    }}
    .time {{
      font-family:'Urbanist', sans-serif;
      font-weight:700;
      font-size:34px;
      line-height:1.1;
      letter-spacing:-1px;
      text-transform:lowercase;
      text-shadow:0px 3px 4px rgba(0,0,0,0.36);
      align-self:flex-end;
      padding-bottom:2px;
    }}
  </style>
</head>
<body>
  <div class="banner">
    <div class="bg"></div>
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
    """Scale title font size down for longer event names to prevent overflow."""
    if len(title) > 30:
        return 80
    if len(title) > 20:
        return 96
    return 120


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
