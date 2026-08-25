"""
Pulls headlines from free public RSS feeds and matches them to assets by
keyword. No API key, no scraping of paywalled content — just RSS, which
sites publish specifically for this kind of reuse.
"""
import logging
from datetime import datetime, timedelta, timezone

import feedparser

from config import NEWS_FEEDS, NEWS_LOOKBACK_DAYS

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
