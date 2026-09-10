"""
Turns per-asset technical + news data into a short, scannable daily digest
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


def build_top_pick_block(scored: dict | None) -> str:
    """scored: output of scoring.pick_top_pick(), or None if nothing was
    eligible today. Shows the full dimension breakdown, not just the pick,
    so the reasoning is visible rather than a black-box single name."""
    title = "*🎯 Today's Top Pick*"

    if scored is None:
        return (
            f"{title}\n_No candidate cleared the bar on every dimension today "
            "(technical conviction, risk/reward, and eligibility) — sitting "
            "this one out is a valid outcome, not a bug._"
        )

    candidate = scored["candidate"]
    asset, ta = candidate["asset"], candidate["ta"]
    base_block = build_asset_block(asset, ta, candidate.get("headlines", []))

    volume_line = (
        f"  • Volume vs 20-day avg: {scored['volume_ratio']:.1f}x"
        if scored["volume_ratio"] else "  • Volume vs 20-day avg: n/a"
    )
    breakdown = (
        f"Composite score: {scored['composite_score']:.2f}/1.00\n"
        f"  • Technical conviction: {scored['technical_conviction']:.2f}/1.00\n"
        f"  • News catalyst strength: {scored['catalyst_strength']:.2f}/1.00\n"
        f"  • Risk/reward ratio: {scored['risk_reward_ratio']:.1f}:1\n"
        f"{volume_line}"
    )

    return f"{title}\n\n{base_block}\n\n{breakdown}"


def build_section(title: str, results: list[dict], empty_note: str) -> str:
    """Generic section builder for any list of {"asset","ta","headlines"}."""
    if not results:
        return f"*{title}*\n_{empty_note}_"
    blocks = [build_asset_block(r["asset"], r["ta"], r["headlines"]) for r in results]
    return f"*{title}*\n\n" + "\n\n".join(blocks)


def build_top_pick_section(pick: dict | None) -> str:
    """pick: output of top_pick.evaluate_candidates(), or None."""
    title = "🎯 Today's Top Pick"

    if pick is None:
        return (
            f"*{title}*\n"
            "_No stock cleared the bar today — technical conviction, "
            "catalyst direction, risk/reward, and liquidity all have to "
            "line up. Sitting this one out is a valid outcome, not a "
            "missing feature._"
        )

    asset, ta, headlines = pick["asset"], pick["ta"], pick["headlines"]
    b = pick["breakdown"]
    block = build_asset_block(asset, ta, headlines)

    score_line = (
        f"Score — technical: {b['technical']*100:.0f}%, "
        f"catalyst: {b['catalyst']*100:.0f}% "
        f"({b['positive_headlines']} positive / {b['negative_headlines']} negative headlines), "
        f"risk/reward: {b['risk_reward_ratio']:.1f}:1, "
        f"volume: {b['volume']*100:.0f}% of the weighted average"
    )

    return f"*{title}*\n\n{block}\n\n_{score_line}_"


def build_report(
    asset_results: list[dict],
    stock_results: list[dict] | None = None,
    swing_results: list[dict] | None = None,
    gem_results: list[dict] | None = None,
    top_pick: dict | None = "unset",
) -> str:
    """asset_results: list of {"asset": ..., "ta": ..., "headlines": [...]}
    stock_results / swing_results / gem_results: same shape, optional
    top_pick: output of top_pick.evaluate_candidates(), or None if nothing
    qualified. Use the sentinel "unset" (default) to omit the section
    entirely rather than showing "no candidate" — lets callers that haven't
    wired up Top Pick yet leave it out cleanly."""
    today = date.today().strftime("%B %d, %Y")
    header = f"📊 *Daily Market Digest — {today}*\n" \
              "Auto-generated technical read + headlines. Not financial advice.\n"

    sections = [header]

    if top_pick != "unset":
        sections.append(build_top_pick_section(top_pick))

    blocks = [build_asset_block(r["asset"], r["ta"], r["headlines"]) for r in asset_results]
    sections.append("\n\n".join(blocks))

    if stock_results:
        stock_blocks = [build_stock_block(r["asset"], r["ta"], r["headlines"]) for r in stock_results]
        sections.append("*📈 Stocks to Watch*")
        sections.append("\n\n".join(stock_blocks))

    if swing_results is not None:
        sections.append(build_section(
            "🚀 Swing Trade Opportunities",
            swing_results,
            "No qualifying bullish setups found in day gainers/most actives this week.",
        ))

    if gem_results is not None:
        sections.append(build_section(
            "💎 Hidden Gem / Growth Candidates",
            gem_results,
            "No qualifying setups found in this week's growth/small-cap screens.",
        ))

    footer = "\n_Rules: trend from price vs SMA20/50/200, momentum from RSI+MACD, " \
             "levels from 20-day swing high/low & ATR. 🔥 = notable news " \
             "(earnings, M&A, ratings changes, etc). Swing/gem picks are " \
             "algorithmically screened from free market data, not personal " \
             "recommendations — small/micro caps carry higher risk and " \
             "volatility. Review before trading._"
    sections.append(footer)

    return "\n\n".join(sections)
