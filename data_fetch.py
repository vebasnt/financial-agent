"""
Pulls daily OHLCV price history for each configured asset using yfinance.
Free, no API key. Yahoo occasionally rate-limits — we retry with backoff.
"""
import time
import logging
import pandas as pd
import yfinance as yf

from config import PRICE_HISTORY_DAYS

log = logging.getLogger(__name__)


def fetch_price_history(ticker: str, retries: int = 3) -> pd.DataFrame:
    """Return a DataFrame with columns Open/High/Low/Close/Volume, or empty
    DataFrame if the fetch failed after retries."""
    period_days = PRICE_HISTORY_DAYS
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(ticker).history(period=f"{period_days}d", interval="1d")
            if df is None or df.empty:
                raise ValueError("empty response")
            df = df.dropna(subset=["Close"])
            return df
        except Exception as e:
            log.warning("fetch failed for %s (attempt %d/%d): %s", ticker, attempt, retries, e)
            time.sleep(2 * attempt)
    log.error("giving up on %s after %d attempts", ticker, retries)
    return pd.DataFrame()


def fetch_all(assets: list[dict]) -> dict:
    """assets: list of {"name", "ticker", ...} dicts from config.ASSETS
    Returns {ticker: DataFrame}"""
    out = {}
    for asset in assets:
        out[asset["ticker"]] = fetch_price_history(asset["ticker"])
    return out
