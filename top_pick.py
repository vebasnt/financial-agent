"""
Combines technical conviction, news catalyst direction, risk/reward quality,
and liquidity into ONE composite score to surface a single best "trade
today" candidate — a genuinely different exercise from the filtered lists
elsewhere in this bot (Swing Trade, Hidden Gems), which just pass/fail a
bar. This module forces a real trade-off between dimensions and requires a
minimum threshold on EACH one, not just a good average.

Draws candidates from pools already computed elsewhere in main.py (stock
watchlist + swing + gem results), so it costs no additional Yahoo Finance
calls — it's pure re-scoring of data you already fetched.
"""
import logging

from config import (
    TOP_PICK_MIN_AVG_DOLLAR_VOLUME,
    TOP_PICK_MIN_RISK_REWARD,
    TOP_PICK_WEIGHTS,
)
from news_fetch import score_catalyst

log = logging.getLogger(__name__)


def _technical_conviction(ta: dict) -> float:
    """0-1: how many independent bullish signals agree — a stock barely
    scraping an overall 'Bullish' call on one signal should score lower
    than one where trend, momentum, and a fresh cross all agree."""
    signals = 0
    total = 5

    if ta["trend"] == "uptrend":
        signals += 2  # the single strongest signal — price above SMA20/50/200
    if ta["golden_cross"] or ta["macd_bull_cross"]:
        signals += 1  # a FRESH signal firing now, not just an old uptrend
    if ta["macd_bullish"]:
        signals += 1  # persistent MACD confirmation
    if 50 <= ta["rsi"] <= 65:
        signals += 1  # healthy momentum zone — not drifting, not overbought

    return min(signals / total, 1.0)


def _risk_reward(ta: dict) -> tuple[float, float | None]:
    """Returns (0-1 score, raw ratio). None ratio means not computable."""
    entry, stop, target = ta.get("entry"), ta.get("stop"), ta.get("target")
    if not all([entry, stop, target]) or entry <= stop:
        return 0.0, None
    rr = (target - entry) / (entry - stop)
    return min(rr / 4, 1.0), rr  # rr of 4:1 or better scores max


def _volume(ta: dict) -> tuple[float, bool]:
    """Returns (0-1 score, passes_liquidity_floor). Liquidity floor is a
    hard gate — a technically perfect setup that's too thin to trade
    shouldn't win regardless of how everything else scores."""
    price = ta.get("price")
    avg_volume = ta.get("avg_volume_20")
    volume_ratio = ta.get("volume_ratio")

    if price is None or avg_volume is None:
        return 0.0, False

    avg_dollar_volume = avg_volume * price
    if avg_dollar_volume < TOP_PICK_MIN_AVG_DOLLAR_VOLUME:
        return 0.0, False

    if volume_ratio is None:
        return 0.5, True
    return min(volume_ratio / 2, 1.0), True  # 2x average volume scores max


def evaluate_candidates(pools: list[list[dict]]) -> dict | None:
    """pools: list of result-lists, e.g. [stock_results, swing_results,
    gem_results] — each a list of {"asset","ta","headlines"} dicts.
    Returns the single best candidate (with a score breakdown attached), or
    None if nothing clears the minimum bar on every dimension."""
    seen_tickers = set()
    scored = []

    for pool in pools:
        for r in pool:
            asset, ta, headlines = r["asset"], r["ta"], r["headlines"]
            ticker = asset["ticker"]

            if ticker in seen_tickers:
                continue  # a stock can appear in multiple pools; score once
            seen_tickers.add(ticker)

            if ta is None or ta["call"] != "Bullish":
                continue

            rr_score, rr_value = _risk_reward(ta)
            if rr_value is None or rr_value < TOP_PICK_MIN_RISK_REWARD:
                continue

            vol_score, passes_liquidity = _volume(ta)
            if not passes_liquidity:
                continue

            tech_score = _technical_conviction(ta)
            catalyst_score, pos_count, neg_count = score_catalyst(headlines)

            composite = (
                tech_score * TOP_PICK_WEIGHTS["technical"]
                + catalyst_score * TOP_PICK_WEIGHTS["catalyst"]
                + rr_score * TOP_PICK_WEIGHTS["risk_reward"]
                + vol_score * TOP_PICK_WEIGHTS["volume"]
            )

            scored.append({
                "asset": asset,
                "ta": ta,
                "headlines": headlines,
                "composite": composite,
                "breakdown": {
                    "technical": round(tech_score, 2),
                    "catalyst": round(catalyst_score, 2),
                    "risk_reward": round(rr_score, 2),
                    "risk_reward_ratio": round(rr_value, 2),
                    "volume": round(vol_score, 2),
                    "positive_headlines": pos_count,
                    "negative_headlines": neg_count,
                },
            })

    if not scored:
        log.info("no candidate cleared the Top Pick bar today")
        return None

    scored.sort(key=lambda x: x["composite"], reverse=True)
    best = scored[0]
    log.info(
        "Top Pick: %s composite=%.2f (tech=%.2f catalyst=%.2f rr=%.2f vol=%.2f)",
        best["asset"]["ticker"], best["composite"],
        best["breakdown"]["technical"], best["breakdown"]["catalyst"],
        best["breakdown"]["risk_reward"], best["breakdown"]["volume"],
    )
    return best
