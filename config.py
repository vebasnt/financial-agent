"""
Central config: which assets to track and where their news comes from.
Edit ASSETS to add/remove tickers. All price data comes from Yahoo Finance
via yfinance (free, no key). All news comes from public RSS feeds (free, no key).
"""

# Each asset: display name, yfinance ticker, category, and keywords used to
# match relevant headlines from the news feeds.
ASSETS = [
    {"name": "Nasdaq Composite", "ticker": "^IXIC", "category": "index",
     "keywords": ["nasdaq"]},
    {"name": "S&P 500", "ticker": "^GSPC", "category": "index",
     "keywords": ["s&p 500", "s&p500", "sp500"]},
    {"name": "Dow Jones", "ticker": "^DJI", "category": "index",
     "keywords": ["dow jones", "dow "]},
    {"name": "BIST 100", "ticker": "XU100.IS", "category": "index",
     "keywords": ["bist", "borsa istanbul"]},
    {"name": "Bitcoin", "ticker": "BTC-USD", "category": "crypto",
     "keywords": ["bitcoin", "btc"]},
    {"name": "Ethereum", "ticker": "ETH-USD", "category": "crypto",
     "keywords": ["ethereum", "eth"]},
    {"name": "Gold", "ticker": "GC=F", "category": "metal",
     "keywords": ["gold price", "gold "]},
    {"name": "Silver", "ticker": "SI=F", "category": "metal",
     "keywords": ["silver price", "silver "]},
]

# Free, no-auth RSS feeds. Add more if you find good ones.
NEWS_FEEDS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://www.investing.com/rss/news_25.rss",       # stock market news
    "https://www.investing.com/rss/news_301.rss",      # commodities
    "https://www.coindesk.com/arc/outboundfeeds/rss/",  # crypto
    "https://feeds.reuters.com/reuters/businessNews",
]

# How many days back to pull news for
NEWS_LOOKBACK_DAYS = 7

# How many days of price history to pull for technical analysis
PRICE_HISTORY_DAYS = 400  # enough for a 200-day SMA

# Max headlines to show per asset in the final report
MAX_HEADLINES_PER_ASSET = 3
