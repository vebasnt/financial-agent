"""
Entry point. Runs daily on weekday mornings (pre-market) via GitHub Actions
cron — see .github/workflows/daily-report.yml.

  python main.py

Pulls price history + news for every asset in config.ASSETS, runs technical
analysis, builds a short digest, and delivers it via email/Slack (whichever
is configured via env vars — see send_report.py).
"""
import logging

from config import (
    ASSETS,
    STOCK_WATCHLIST,
    SWING_SCREENS,
    GEM_SCREENS,
    MAX_SWING_CANDIDATES_TO_ANALYZE,
    MAX_GEM_CANDIDATES_TO_ANALYZE,
    SWING_TOP_N,
    GEM_TOP_N,
)
from data_fetch import fetch_all, fetch_price_history
from technical_analysis import analyze
from news_fetch import (
    fetch_headlines,
    match_headlines_to_asset,
    fetch_stock_headlines,
    tag_notable,
)
from screener import get_screener_candidates, scan_for_setups
from top_pick import evaluate_candidates
from report import build_report
from send_report import deliver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _to_results(scanned: list[tuple[dict, dict]], top_n: int) -> list[dict]:
    """Turns scan_for_setups() output into the {"asset","ta","headlines"}
    shape the report builder expects, fetching news only for the final
    top N (not every candidate scanned) to keep API calls reasonable."""
    results = []
    for candidate, ta in scanned[:top_n]:
        headlines = fetch_stock_headlines(candidate["ticker"])
        headlines = tag_notable(headlines)
        results.append({"asset": candidate, "ta": ta, "headlines": headlines})
    return results


def run() -> str:
    log.info("fetching price data for %d broad-market assets", len(ASSETS))
    price_data = fetch_all(ASSETS)

    log.info("fetching general market news")
    all_headlines = fetch_headlines()
    log.info("got %d headlines total", len(all_headlines))

    results = []
    for asset in ASSETS:
        df = price_data.get(asset["ticker"])
        ta = analyze(df) if df is not None else None
        headlines = match_headlines_to_asset(all_headlines, asset["keywords"], limit=5)
        headlines = tag_notable(headlines)
        results.append({"asset": asset, "ta": ta, "headlines": headlines})

    log.info("fetching price data + dedicated news for %d watchlist stocks", len(STOCK_WATCHLIST))
    stock_results = []
    for stock in STOCK_WATCHLIST:
        df = fetch_price_history(stock["ticker"])
        ta = analyze(df) if df is not None else None
        headlines = fetch_stock_headlines(stock["ticker"])
        headlines = tag_notable(headlines)
        stock_results.append({"asset": stock, "ta": ta, "headlines": headlines})

    watchlist_tickers = {s["ticker"] for s in STOCK_WATCHLIST}

    log.info("scanning swing-trade screens: %s", SWING_SCREENS)
    swing_candidates = get_screener_candidates(SWING_SCREENS)
    log.info("got %d raw swing candidates", len(swing_candidates))
    swing_scanned = scan_for_setups(
        swing_candidates,
        max_to_analyze=MAX_SWING_CANDIDATES_TO_ANALYZE,
        exclude_tickers=watchlist_tickers,
    )
    swing_results = _to_results(swing_scanned, SWING_TOP_N)
    log.info("found %d qualifying swing setups", len(swing_results))

    log.info("scanning hidden-gem screens: %s", GEM_SCREENS)
    gem_candidates = get_screener_candidates(GEM_SCREENS)
    log.info("got %d raw gem candidates", len(gem_candidates))
    gem_scanned = scan_for_setups(
        gem_candidates,
        max_to_analyze=MAX_GEM_CANDIDATES_TO_ANALYZE,
        exclude_tickers=watchlist_tickers,
    )
    gem_results = _to_results(gem_scanned, GEM_TOP_N)
    log.info("found %d qualifying gem candidates", len(gem_results))

    log.info("evaluating Today's Top Pick across all stock pools")
    top_pick = evaluate_candidates([stock_results, swing_results, gem_results])

    report_text = build_report(results, stock_results, swing_results, gem_results, top_pick)
    deliver(report_text)
    return report_text


if __name__ == "__main__":
    run()
