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

# Individual stocks to watch. Unlike ASSETS above (which are matched against
# broad market feeds by keyword), each of these gets its OWN dedicated Yahoo
# Finance news feed per ticker — much more precise, since it only returns
# headlines actually about that company. Add/remove tickers freely; any
# valid Yahoo Finance ticker works (check the symbol on finance.yahoo.com).
STOCK_WATCHLIST = [
    {"name": "Apple", "ticker": "AAPL"},
    {"name": "Microsoft", "ticker": "MSFT"},
    {"name": "Nvidia", "ticker": "NVDA"},
    {"name": "Amazon", "ticker": "AMZN"},
    {"name": "Alphabet (Google)", "ticker": "GOOGL"},
    {"name": "Meta", "ticker": "META"},
    {"name": "Tesla", "ticker": "TSLA"},
]

# Free, no-auth RSS feeds for the broad-market ASSETS above. Add more if you
# find good ones.
NEWS_FEEDS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://www.investing.com/rss/news_25.rss",       # stock market news
    "https://www.investing.com/rss/news_301.rss",      # commodities
    "https://www.coindesk.com/arc/outboundfeeds/rss/",  # crypto
    "https://feeds.reuters.com/reuters/businessNews",
]

# Per-ticker Yahoo Finance news feed template, used for STOCK_WATCHLIST.
# Free, no key. Fill in the ticker symbol.
STOCK_NEWS_FEED_TEMPLATE = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
)

# Headline is flagged "notable" (highlighted in the report, and exempt from
# the per-asset headline cap) if its title contains any of these — keep this
# list focused on genuinely market-moving language, not routine coverage.
NOTABLE_KEYWORDS = [
    "earnings", "beats", "misses", "guidance", "upgrade", "downgrade",
    "acquisition", "acquires", "merger", "lawsuit", "recall", "resign",
    "ceo", "layoffs", "bankruptcy", "sec probe", "investigation",
    "halted", "surge", "plunge", "soar", "crash", "record high",
    "record low", "buyback", "dividend cut", "fraud", "hack", "breach",
    "fda approval", "antitrust",
]

# --- Swing trade / hidden gem discovery ---
# Uses yfinance's free built-in Yahoo screeners (no key, no paid screener
# needed) to surface candidates beyond the fixed watchlist above, then runs
# the same technical rules on whatever surfaces to filter for genuine setups.

# Screens used to find short-term momentum/swing candidates.
SWING_SCREENS = ["day_gainers", "most_actives"]

# Screens used to find smaller, higher-growth "hidden gem" candidates —
# small_cap_gainers (<$2B market cap), aggressive_small_caps (low recent EPS
# growth but building), growth_technology_stocks (25%+ revenue & EPS growth),
# undervalued_growth_stocks (cheap PE/PEG with 25%+ EPS growth).
GEM_SCREENS = [
    "small_cap_gainers",
    "aggressive_small_caps",
    "growth_technology_stocks",
    "undervalued_growth_stocks",
]

MAX_CANDIDATES_PER_SCREEN = 15    # how many raw results to pull per screen
MAX_SWING_CANDIDATES_TO_ANALYZE = 20   # cap on how many get full TA (keeps runtime sane)
MAX_GEM_CANDIDATES_TO_ANALYZE = 40
SWING_TOP_N = 5     # how many make it into the final report
GEM_TOP_N = 5

# How many days back to pull news for
NEWS_LOOKBACK_DAYS = 7

# How many days of price history to pull for technical analysis
PRICE_HISTORY_DAYS = 400  # enough for a 200-day SMA

# Max headlines to show per asset in the final report (notable headlines are
# always shown in addition to this cap, not counted against it)
MAX_HEADLINES_PER_ASSET = 3

# Max stocks' worth of headlines to fetch per ticker before filtering
MAX_HEADLINES_PER_STOCK_FETCH = 10
