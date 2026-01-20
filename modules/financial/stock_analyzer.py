"""
Atlas Personal OS - Stock Analyzer

Fetch and analyze stock market data. Works offline with cached data,
optionally fetches live data when yfinance is installed.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional
from decimal import Decimal

from modules.core.database import Database, get_database

# Optional yfinance import
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class StockAnalyzer:
    """Stock market data analyzer with local caching."""

    STOCKS_TABLE = "stocks"
    STOCKS_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        name TEXT,
        sector TEXT,
        industry TEXT,
        currency TEXT DEFAULT 'USD',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    PRICES_TABLE = "stock_prices"
    PRICES_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        date DATE NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(symbol, date)
    """

    WATCHLIST_TABLE = "watchlist"
    WATCHLIST_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL UNIQUE,
        target_price REAL,
        notes TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize stock analyzer with database."""
        self.db = db or get_database()
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create required tables if they don't exist."""
        self.db.create_table(self.STOCKS_TABLE, self.STOCKS_SCHEMA)
        self.db.create_table(self.PRICES_TABLE, self.PRICES_SCHEMA)
        self.db.create_table(self.WATCHLIST_TABLE, self.WATCHLIST_SCHEMA)

    def fetch_stock_info(self, symbol: str) -> Optional[dict]:
        """
        Fetch stock info from Yahoo Finance and cache it.
        Requires yfinance to be installed.
        """
        if not YFINANCE_AVAILABLE:
            return self._get_cached_stock_info(symbol)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            stock_data = {
                "symbol": symbol.upper(),
                "name": info.get("shortName", info.get("longName", "")),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "currency": info.get("currency", "USD"),
            }

            # Upsert into database
            existing = self.db.fetchone(
                f"SELECT id FROM {self.STOCKS_TABLE} WHERE symbol = ?",
                (symbol.upper(),)
            )

            if existing:
                self.db.update(
                    self.STOCKS_TABLE,
                    stock_data,
                    "symbol = ?",
                    (symbol.upper(),)
                )
            else:
                self.db.insert(self.STOCKS_TABLE, stock_data)

            return stock_data
        except Exception:
            return self._get_cached_stock_info(symbol)

    def _get_cached_stock_info(self, symbol: str) -> Optional[dict]:
        """Get cached stock info from database."""
        row = self.db.fetchone(
            f"SELECT * FROM {self.STOCKS_TABLE} WHERE symbol = ?",
            (symbol.upper(),)
        )
        return dict(row) if row else None

    def fetch_price_history(
        self,
        symbol: str,
        period: str = "1mo",
        force_refresh: bool = False
    ) -> list[dict]:
        """
        Fetch price history from Yahoo Finance and cache it.

        Args:
            symbol: Stock symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            force_refresh: Force fetch even if cached data exists
        """
        symbol = symbol.upper()

        # Check cache first
        if not force_refresh:
            cached = self._get_cached_prices(symbol)
            if cached:
                return cached

        if not YFINANCE_AVAILABLE:
            return self._get_cached_prices(symbol)

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            prices = []
            for idx, row in hist.iterrows():
                price_data = {
                    "symbol": symbol,
                    "date": idx.date().isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
                prices.append(price_data)

                # Cache in database
                try:
                    self.db.insert(self.PRICES_TABLE, price_data)
                except Exception:
                    # Update if exists
                    self.db.update(
                        self.PRICES_TABLE,
                        price_data,
                        "symbol = ? AND date = ?",
                        (symbol, price_data["date"])
                    )

            return prices
        except Exception:
            return self._get_cached_prices(symbol)

    def _get_cached_prices(self, symbol: str, days: int = 365) -> list[dict]:
        """Get cached price history from database."""
        start_date = (date.today() - timedelta(days=days)).isoformat()
        rows = self.db.fetchall(
            f"SELECT * FROM {self.PRICES_TABLE} WHERE symbol = ? AND date >= ? ORDER BY date",
            (symbol.upper(), start_date)
        )
        return [dict(row) for row in rows]

    def get_latest_price(self, symbol: str) -> Optional[dict]:
        """Get the most recent price for a symbol."""
        row = self.db.fetchone(
            f"SELECT * FROM {self.PRICES_TABLE} WHERE symbol = ? ORDER BY date DESC LIMIT 1",
            (symbol.upper(),)
        )
        return dict(row) if row else None

    def add_manual_price(
        self,
        symbol: str,
        price_date: date,
        close: float,
        open_price: Optional[float] = None,
        high: Optional[float] = None,
        low: Optional[float] = None,
        volume: int = 0
    ) -> bool:
        """Manually add a price entry (useful when API is unavailable)."""
        data = {
            "symbol": symbol.upper(),
            "date": price_date.isoformat(),
            "close": close,
            "open": open_price or close,
            "high": high or close,
            "low": low or close,
            "volume": volume,
        }
        try:
            self.db.insert(self.PRICES_TABLE, data)
            return True
        except Exception:
            return False

    # Watchlist management
    def add_to_watchlist(
        self,
        symbol: str,
        target_price: Optional[float] = None,
        notes: str = ""
    ) -> bool:
        """Add a stock to watchlist."""
        try:
            data = {
                "symbol": symbol.upper(),
                "target_price": target_price,
                "notes": notes,
            }
            self.db.insert(self.WATCHLIST_TABLE, data)
            return True
        except Exception:
            return False

    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove a stock from watchlist."""
        rows_deleted = self.db.delete(
            self.WATCHLIST_TABLE,
            "symbol = ?",
            (symbol.upper(),)
        )
        return rows_deleted > 0

    def get_watchlist(self) -> list[dict]:
        """Get all stocks in watchlist with latest prices."""
        rows = self.db.fetchall(
            f"SELECT * FROM {self.WATCHLIST_TABLE} ORDER BY symbol"
        )
        watchlist = []
        for row in rows:
            item = dict(row)
            latest = self.get_latest_price(item["symbol"])
            if latest:
                item["latest_price"] = latest["close"]
                item["price_date"] = latest["date"]
            watchlist.append(item)
        return watchlist

    # Analysis functions
    def calculate_returns(self, symbol: str, days: int = 30) -> Optional[dict]:
        """Calculate returns over a period."""
        prices = self._get_cached_prices(symbol, days)
        if len(prices) < 2:
            return None

        start_price = prices[0]["close"]
        end_price = prices[-1]["close"]

        return {
            "symbol": symbol.upper(),
            "start_date": prices[0]["date"],
            "end_date": prices[-1]["date"],
            "start_price": start_price,
            "end_price": end_price,
            "absolute_return": end_price - start_price,
            "percent_return": ((end_price - start_price) / start_price) * 100,
            "days": len(prices),
        }

    def calculate_moving_average(
        self,
        symbol: str,
        window: int = 20
    ) -> Optional[float]:
        """Calculate simple moving average."""
        prices = self._get_cached_prices(symbol, window * 2)
        if len(prices) < window:
            return None

        recent_prices = [p["close"] for p in prices[-window:]]
        return sum(recent_prices) / len(recent_prices)

    def get_price_range(self, symbol: str, days: int = 30) -> Optional[dict]:
        """Get high/low price range for a period."""
        prices = self._get_cached_prices(symbol, days)
        if not prices:
            return None

        highs = [p["high"] for p in prices]
        lows = [p["low"] for p in prices]

        return {
            "symbol": symbol.upper(),
            "period_days": days,
            "high": max(highs),
            "low": min(lows),
            "range": max(highs) - min(lows),
            "current": prices[-1]["close"] if prices else None,
        }

    def is_yfinance_available(self) -> bool:
        """Check if yfinance is installed for live data."""
        return YFINANCE_AVAILABLE
