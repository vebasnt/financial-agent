"""
Computes technical indicators from OHLCV data and turns them into a simple
rule-based read: trend direction, momentum state, and support/resistance
levels. This is intentionally simple and transparent (not a black box) so
you can see exactly why a call was made and tune the rules yourself.
"""
import pandas as pd
import ta


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adds SMA20/50/200, RSI14, MACD, MACD signal, ATR14 columns."""
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["RSI14"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()

    df["ATR14"] = ta.volatility.AverageTrueRange(
        df["High"], df["Low"], df["Close"], window=14
    ).average_true_range()

    return df


def recent_support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
    """Simple swing high/low over the last `lookback` sessions."""
    recent = df.tail(lookback)
    return float(recent["Low"].min()), float(recent["High"].max())


def analyze(df: pd.DataFrame) -> dict | None:
    """Returns a dict summarizing the technical picture for one asset, or
    None if there isn't enough data."""
    if df.empty or len(df) < 60:
        return None

    df = compute_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(last["Close"])
    sma20, sma50 = float(last["SMA20"]), float(last["SMA50"])
    sma200 = float(last["SMA200"]) if not pd.isna(last["SMA200"]) else None
    rsi = float(last["RSI14"])
    macd, macd_sig = float(last["MACD"]), float(last["MACD_signal"])
    macd_prev, macd_sig_prev = float(prev["MACD"]), float(prev["MACD_signal"])
    atr = float(last["ATR14"])

    # --- Trend: price vs moving averages ---
    trend_votes = 0
    trend_votes += 1 if price > sma20 else -1
    trend_votes += 1 if price > sma50 else -1
    if sma200 is not None:
        trend_votes += 1 if price > sma200 else -1

    if trend_votes >= 2:
        trend = "uptrend"
    elif trend_votes <= -2:
        trend = "downtrend"
    else:
        trend = "sideways"

    golden_cross = sma200 is not None and sma50 > sma200 and float(df.iloc[-2]["SMA50"]) <= float(df.iloc[-2]["SMA200"])
    death_cross = sma200 is not None and sma50 < sma200 and float(df.iloc[-2]["SMA50"]) >= float(df.iloc[-2]["SMA200"])

    # --- Momentum ---
    if rsi >= 70:
        momentum = "overbought"
    elif rsi <= 30:
        momentum = "oversold"
    else:
        momentum = "neutral"

    macd_bull_cross = macd_prev <= macd_sig_prev and macd > macd_sig
    macd_bear_cross = macd_prev >= macd_sig_prev and macd < macd_sig

    # --- Combine into an overall call ---
    score = 0
    score += 1 if trend == "uptrend" else (-1 if trend == "downtrend" else 0)
    score += 1 if macd > macd_sig else -1
    if momentum == "overbought":
        score -= 1  # extended, more caution
    if momentum == "oversold":
        score += 1  # potential bounce
    if golden_cross:
        score += 1
    if death_cross:
        score -= 1

    if score >= 2:
        call = "Bullish"
    elif score <= -2:
        call = "Bearish"
    else:
        call = "Neutral"

    support, resistance = recent_support_resistance(df, lookback=20)

    # Suggested trade levels (simple ATR/swing based, not investment advice)
    if call == "Bullish":
        entry = price
        stop = round(min(support, price - 1.5 * atr), 4)
        target = round(price + 2 * (price - stop), 4)
    elif call == "Bearish":
        entry = price
        stop = round(max(resistance, price + 1.5 * atr), 4)
        target = round(price - 2 * (stop - price), 4)
    else:
        entry = stop = target = None

    return {
        "price": price,
        "trend": trend,
        "momentum": momentum,
        "rsi": rsi,
        "macd_bull_cross": macd_bull_cross,
        "macd_bear_cross": macd_bear_cross,
        "golden_cross": golden_cross,
        "death_cross": death_cross,
        "support": support,
        "resistance": resistance,
        "call": call,
        "score": score,
        "entry": entry,
        "stop": stop,
        "target": target,
        "atr": atr,
    }
