"""
Discovers stock candidates beyond the fixed watchlist using yfinance's free
built-in Yahoo Finance screeners (no API key, no paid screener). This is
just candidate SOURCING — technical_analysis.analyze() still does the actual
filtering for genuine setups, exactly like it does for the watchlist.
"""
import time
import logging

import yfinance as yf

from config import MAX_CANDIDATES_PER_SCREEN
from data_fetch import fetch_price_history
from technical_analysis import analyze

log = logging.getLogger(__name__)


def get_screener_candidates(screen_names: list[str]) -> list[dict]:
    """Pulls raw candidates from one or more predefined Yahoo screens.
    Returns deduped list of {"name", "ticker"}."""
    seen = set()
    candidates = []
    for screen_name in screen_names:
        try:
            result = yf.screen(screen_name, count=MAX_CANDIDATES_PER_SCREEN)
        except Exception as e:
            log.warning("screener query '%s' failed: %s", screen_name, e)
            continue

        quotes = (result or {}).get("quotes", [])
        for q in quotes:
            symbol = q.get("symbol")
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            candidates.append({
                "name": q.get("shortName") or q.get("longName") or symbol,
                "ticker": symbol,
            })

    return candidates


def scan_for_setups(
    candidates: list[dict],
    max_to_analyze: int,
    exclude_tickers: set | None = None,
    require_fresh_signal: bool = False,
) -> list[tuple[dict, dict]]:
    """Runs full technical analysis on candidates and keeps only genuine
    bullish setups (not already overbought). Returns list of (asset, ta)
    tuples sorted best-first. Caps how many tickers get analyzed to keep
    runtime and Yahoo rate limits in check."""
    exclude_tickers = exclude_tickers or set()
    scored = []
    analyzed = 0

    for candidate in candidates:
        ticker = candidate["ticker"]
        if ticker in exclude_tickers:
            continue
        if analyzed >= max_to_analyze:
            break
        analyzed += 1

        df = fetch_price_history(ticker)
        time.sleep(0.3)  # be polite to Yahoo between many rapid requests
        if df is None or df.empty:
            continue

        ta = analyze(df)
        if ta is None:
            continue

        # Only genuine bullish setups — extended/overbought names are a
        # worse swing entry even if the overall call is still "Bullish".
        if ta["call"] != "Bullish" or ta["momentum"] == "overbought":
            continue

        fresh_signal = ta["golden_cross"] or ta["macd_bull_cross"]
        if require_fresh_signal and not fresh_signal:
            continue

        # Rank fresher signals (recent cross) above merely-trending ones
        rank_score = ta["score"] + (1 if fresh_signal else 0)
        scored.append((rank_score, candidate, ta))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(candidate, ta) for _, candidate, ta in scored]
