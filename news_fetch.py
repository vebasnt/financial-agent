"""
Pulls headlines from free public RSS feeds and matches them to assets by
keyword. No API key, no scraping of paywalled content — just RSS, which
sites publish specifically for this kind of reuse.
"""
import logging
from datetime import datetime, timedelta, timezone

import feedparser

from config import (
    NEWS_FEEDS,
    NEWS_LOOKBACK_DAYS,
    STOCK_NEWS_FEED_TEMPLATE,
    MAX_HEADLINES_PER_STOCK_FETCH,
    NOTABLE_KEYWORDS,
)

log = logging.getLogger(__name__)


def _entry_datetime(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def fetch_headlines() -> list[dict]:
    """Returns a flat list of {"title", "link", "published", "source"} from
    all configured feeds, deduplicated by title."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=NEWS_LOOKBACK_DAYS)
    seen_titles = set()
    headlines = []

    for feed_url in NEWS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            log.warning("failed to parse feed %s: %s", feed_url, e)
            continue

        source = parsed.feed.get("title", feed_url) if parsed.feed else feed_url

        for entry in parsed.entries:
            title = entry.get("title", "").strip()
            if not title or title.lower() in seen_titles:
                continue
            published = _entry_datetime(entry)
            if published and published < cutoff:
                continue
            seen_titles.add(title.lower())
            headlines.append({
                "title": title,
                "link": entry.get("link", ""),
                "published": published,
                "source": source,
            })

    return headlines


def match_headlines_to_asset(headlines: list[dict], keywords: list[str], limit: int) -> list[dict]:
    """Case-insensitive keyword match against headline titles."""
    matched = []
    for h in headlines:
        title_lower = h["title"].lower()
        if any(kw.lower() in title_lower for kw in keywords):
            matched.append(h)
        if len(matched) >= limit:
            break
    return matched


def fetch_stock_headlines(ticker: str) -> list[dict]:
    """Pulls headlines from Yahoo Finance's dedicated per-ticker news feed —
    much more precise than keyword-matching broad feeds, since every result
    is already specifically about this company."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=NEWS_LOOKBACK_DAYS)
    feed_url = STOCK_NEWS_FEED_TEMPLATE.format(ticker=ticker)

    try:
        parsed = feedparser.parse(feed_url)
    except Exception as e:
        log.warning("failed to parse stock feed for %s: %s", ticker, e)
        return []

    source = parsed.feed.get("title", f"Yahoo Finance ({ticker})") if parsed.feed else ticker
    headlines = []
    seen_titles = set()

    for entry in parsed.entries[:MAX_HEADLINES_PER_STOCK_FETCH]:
        title = entry.get("title", "").strip()
        if not title or title.lower() in seen_titles:
            continue
        published = _entry_datetime(entry)
        if published and published < cutoff:
            continue
        seen_titles.add(title.lower())
        headlines.append({
            "title": title,
            "link": entry.get("link", ""),
            "published": published,
            "source": source,
        })

    return headlines


def is_notable(headline_title: str) -> bool:
    """True if the headline contains genuinely market-moving language
    (earnings, M&A, ratings changes, etc.) rather than routine coverage."""
    title_lower = headline_title.lower()
    return any(kw in title_lower for kw in NOTABLE_KEYWORDS)


def tag_notable(headlines: list[dict]) -> list[dict]:
    """Adds an in-place 'notable' bool to each headline dict and returns it,
    sorted so notable headlines come first."""
    for h in headlines:
        h["notable"] = is_notable(h["title"])
    return sorted(headlines, key=lambda h: not h["notable"])
