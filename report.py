"""
Turns per-asset technical + news data into a short, scannable weekly digest
(Slack/email style: emoji, short lines, no fluff).
"""
from datetime import date

from config import MAX_HEADLINES_PER_ASSET

CALL_EMOJI = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}


def _fmt_price(p: float) -> str:
    if p is None:
        return "n/a"
    return f"{p:,.4f}" if p < 10 else f"{p:,.2f}"


def build_asset_block(asset: dict, ta: dict | None, headlines: list[dict]) -> str:
    name = asset["name"]
    if ta is None:
        return f"*{name}* — ⚠️ no data available this week"

    emoji = CALL_EMOJI.get(ta["call"], "⚪")
    lines = [f"{emoji} *{name}* ({asset['ticker']}) — {ta['call']}"]
    lines.append(
        f"Price: {_fmt_price(ta['price'])} | Trend: {ta['trend']} | "
        f"RSI: {ta['rsi']:.0f} ({ta['momentum']})"
    )

    flags = []
    if ta["golden_cross"]:
        flags.append("golden cross (50>200 SMA)")
    if ta["death_cross"]:
        flags.append("death cross (50<200 SMA)")
    if ta["macd_bull_cross"]:
        flags.append("MACD bullish cross")
    if ta["macd_bear_cross"]:
        flags.append("MACD bearish cross")
    if flags:
        lines.append("Signals: " + ", ".join(flags))

    lines.append(
        f"Support: {_fmt_price(ta['support'])} | Resistance: {_fmt_price(ta['resistance'])}"
    )

    if ta["call"] in ("Bullish", "Bearish"):
        lines.append(
            f"Trade idea: entry ~{_fmt_price(ta['entry'])}, "
            f"stop {_fmt_price(ta['stop'])}, target {_fmt_price(ta['target'])} "
            f"(rule-based, not financial advice)"
        )

    if headlines:
        notable = [h for h in headlines if h.get("notable")]
        routine = [h for h in headlines if not h.get("notable")][:MAX_HEADLINES_PER_ASSET]
        shown = notable + routine
        lines.append("News:")
        for h in shown:
            prefix = "🔥 " if h.get("notable") else "  • "
            lines.append(f"{prefix}{h['title']} ({h['source']})")

    return "\n".join(lines)


def build_stock_block(stock: dict, ta: dict | None, headlines: list[dict]) -> str:
    """Same shape as build_asset_block but for individual watchlist stocks —
    kept as a thin wrapper since the format is identical, just labeled
    separately in the report."""
    return build_asset_block(stock, ta, headlines)


def build_report(asset_results: list[dict], stock_results: list[dict] | None = None) -> str:
    """asset_results: list of {"asset": ..., "ta": ..., "headlines": [...]}
    stock_results: same shape, for individual watchlist stocks (optional)"""
    today = date.today().strftime("%B %d, %Y")
    header = f"📊 *Weekly Market Digest — {today}*\n" \
              "Auto-generated technical read + headlines. Not financial advice.\n"

    blocks = [build_asset_block(r["asset"], r["ta"], r["headlines"]) for r in asset_results]

    sections = [header, "\n\n".join(blocks)]

    if stock_results:
        stock_blocks = [build_stock_block(r["asset"], r["ta"], r["headlines"]) for r in stock_results]
        sections.append("*📈 Stocks to Watch*")
        sections.append("\n\n".join(stock_blocks))

    footer = "\n_Rules: trend from price vs SMA20/50/200, momentum from RSI+MACD, " \
             "levels from 20-day swing high/low & ATR. 🔥 = notable news " \
             "(earnings, M&A, ratings changes, etc). Review before trading._"
    sections.append(footer)

    return "\n\n".join(sections)
