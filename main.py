"""
Entry point. Run weekly (Monday, pre-market) via GitHub Actions cron.

  python main.py

Pulls price history + news for every asset in config.ASSETS, runs technical
analysis, builds a short digest, and delivers it via email/Slack (whichever
is configured via env vars — see send_report.py).
"""
import logging

from config import ASSETS
from data_fetch import fetch_all
from technical_analysis import analyze
from news_fetch import fetch_headlines, match_headlines_to_asset
from report import build_report
from send_report import deliver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run() -> str:
    log.info("fetching price data for %d assets", len(ASSETS))
    price_data = fetch_all(ASSETS)

    log.info("fetching news headlines")
    all_headlines = fetch_headlines()
    log.info("got %d headlines total", len(all_headlines))

    results = []
    for asset in ASSETS:
        df = price_data.get(asset["ticker"])
        ta = analyze(df) if df is not None else None
        headlines = match_headlines_to_asset(all_headlines, asset["keywords"], limit=5)
        results.append({"asset": asset, "ta": ta, "headlines": headlines})

    report_text = build_report(results)
    deliver(report_text)
    return report_text


if __name__ == "__main__":
    run()
