# Weekly Market Digest Agent

Fully automated, free-data agent that every **Monday** pulls prices + news for
Nasdaq, S&P 500, Dow, BIST 100, Bitcoin, Ethereum, Gold, and Silver, runs
basic technical analysis, and sends you a short digest with rule-based trade
ideas (entry / stop / target).

**Not financial advice** — it's a transparent, rule-based read (moving
averages, RSI, MACD, recent swing highs/lows), not a prediction.

## How it works

| File | Role |
|---|---|
| `config.py` | List of tracked assets & news feeds — edit this to add/remove tickers |
| `data_fetch.py` | Pulls OHLCV price history from Yahoo Finance (`yfinance`, free) |
| `technical_analysis.py` | Computes SMA/RSI/MACD/ATR and turns them into Bullish/Bearish/Neutral + levels |
| `news_fetch.py` | Pulls headlines from free RSS feeds, matches them to assets by keyword |
| `report.py` | Builds the short Slack/email-style digest text |
| `send_report.py` | Sends the digest via email (SMTP) and/or Slack webhook |
| `main.py` | Orchestrates everything — this is what runs each week |
| `.github/workflows/weekly-report.yml` | Runs `main.py` automatically every Monday via GitHub Actions (free) |

## Setup (5–10 minutes)

1. **Create a GitHub repo** and push this folder to it.

2. **Choose delivery channel(s)** and add the matching secrets under
   `Repo → Settings → Secrets and variables → Actions → New repository secret`:

   **Email** (e.g. Gmail):
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = your Gmail address
   - `SMTP_PASS` = a Gmail **App Password** (not your real password — create
     one at https://myaccount.google.com/apppasswords, requires 2FA enabled)
   - `EMAIL_TO` = where to send the digest

   **Slack**:
   - `SLACK_WEBHOOK_URL` = an Incoming Webhook URL from
     https://api.slack.com/messaging/webhooks

   You can set up both, one, or neither (if neither, the report just prints
   to the Actions log so you can copy it manually).

3. **That's it.** The workflow is scheduled for `0 11 * * 1` (11:00 UTC every
   Monday). Edit the cron line in `.github/workflows/weekly-report.yml` to
   change the time.

4. **Test it immediately** without waiting for Monday: go to your repo's
   `Actions` tab → `Weekly Market Digest` → `Run workflow` (this works because
   of the `workflow_dispatch` trigger).

## Running locally

```bash
pip install -r requirements.txt
python main.py
```

Without SMTP/Slack env vars set, it just prints the report to your terminal
— good for testing changes to the logic before deploying.

## Tuning it

- **Add/remove assets**: edit `ASSETS` in `config.py`. Any Yahoo Finance
  ticker works (check on finance.yahoo.com — e.g. Apple would be `AAPL`).
- **Add more news sources**: add RSS feed URLs to `NEWS_FEEDS` in
  `config.py`.
- **Change the signal rules**: everything is in `technical_analysis.py`,
  in plain, readable Python — no black box. Adjust the scoring in `analyze()`
  to make it more/less aggressive, or add indicators (Bollinger Bands,
  volume analysis, etc.) using the `ta` library.

## Known limitations

- `yfinance` is an unofficial wrapper around Yahoo Finance and can
  occasionally rate-limit or change format — `data_fetch.py` retries 3x, but
  if it fails for one asset the report will just show "no data available"
  for that one instead of crashing the whole run.
- News matching is simple keyword-based (not NLP sentiment) — headlines are
  shown as context for you to read, not scored automatically.
- This is a **rules-based technical read**, not a backtested trading
  strategy — treat trade ideas as a starting point for your own research,
  not a signal to act on blindly.
