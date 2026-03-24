# Event Poster API

Generates event poster + banner PNGs from Airtable data and posts them to Slack for feedback.

## How it works

```
Airtable (status → "Design")
  → Make.com webhook trigger
  → POST /generate  (this API)
  → Playwright renders HTML → PNG
  → Uploads poster.png + banner.png to Slack
  → Posts feedback request message
```

---

## Deploy to Render (free tier)

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repo — Render detects `render.yaml` automatically
4. Add environment variables in the Render dashboard:
   - `SLACK_BOT_TOKEN` — your Slack bot token (see below)
   - `SLACK_CHANNEL` — e.g. `#design-feedback`
   - `API_SECRET` — auto-generated, **copy this**, you'll need it for Make.com
5. Deploy — first build takes ~3 min (installs Chromium)

Your API will be live at: `https://poster-api.onrender.com`

---

## Slack Bot Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. Add these **Bot Token Scopes**:
   - `files:write`
   - `chat:write`
   - `channels:join`
3. Install app to workspace → copy the **Bot User OAuth Token**
4. Invite the bot to your channel: `/invite @your-bot-name`

---

## Make.com Scenario

Create a scenario with these modules:

**1. Airtable — Watch Records**
- Connection: your Airtable account
- Base: your events base
- Table: your events table
- Filter: `Status = "Design"`

**2. HTTP — Make a Request**
- URL: `https://your-app.onrender.com/generate`
- Method: `POST`
- Headers:
  - `X-API-Secret`: your `API_SECRET` from Render
  - `Content-Type`: `application/json`
- Body (JSON):
```json
{
  "title": "{{1.Title}}",
  "date": "{{1.Date}}",
  "time": "{{1.Time}}",
  "image_url": "{{1.Image[].url}}",
  "record_id": "{{1.Record ID}}"
}
```

---

## API Reference

### `POST /generate`

**Headers:**
```
X-API-Secret: your-secret
Content-Type: application/json
```

**Body:**
```json
{
  "title": "Retas de Ajedréz",
  "date": "miércoles, 24 marzo",
  "time": "6:00 pm",
  "image_url": "https://...",
  "record_id": "recXXXXXXXX"
}
```

**Response:**
```json
{
  "status": "posted",
  "slack": {
    "ok": true,
    "ts": "1711234567.000100",
    "poster_uploaded": true,
    "banner_uploaded": true
  }
}
```

### `GET /health`
Returns `{"status": "ok"}` — use this to verify the service is running.

---

## Local Development

```bash
pip install -r requirements.txt
playwright install chromium

export API_SECRET=test
export SLACK_BOT_TOKEN=xoxb-your-token
export SLACK_CHANNEL=#design-feedback

python app.py
```

Test with curl:
```bash
curl -X POST http://localhost:5000/generate \
  -H "X-API-Secret: test" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Retas de Ajedréz",
    "date": "miércoles, 24 marzo",
    "time": "6:00 pm",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/ChessSet.jpg/1280px-ChessSet.jpg",
    "record_id": "rec123"
  }'
```
