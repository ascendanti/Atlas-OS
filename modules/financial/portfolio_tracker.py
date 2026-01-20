"""
Atlas Personal OS - Portfolio Tracker

Track investment holdings, calculate returns, and monitor portfolio performance.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from modules.core.database import Database, get_database
from modules.financial.stock_analyzer import StockAnalyzer


class PortfolioTracker:
    """Investment portfolio tracking system."""

    HOLDINGS_TABLE = "portfolio_holdings"
    HOLDINGS_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        shares REAL NOT NULL,
        cost_basis REAL NOT NULL,
        purchase_date DATE NOT NULL,
        account TEXT DEFAULT 'default',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    TRANSACTIONS_TABLE = "portfolio_transactions"
    TRANSACTIONS_SCHEMA = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        shares REAL NOT NULL,
        price REAL NOT NULL,
        total_amount REAL NOT NULL,
        fees REAL DEFAULT 0,
        transaction_date DATE NOT NULL,
        account TEXT DEFAULT 'default',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize portfolio tracker with database."""
        self.db = db or get_database()
        self.stock_analyzer = StockAnalyzer(db)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create required tables if they don't exist."""
        self.db.create_table(self.HOLDINGS_TABLE, self.HOLDINGS_SCHEMA)
        self.db.create_table(self.TRANSACTIONS_TABLE, self.TRANSACTIONS_SCHEMA)

    def buy(
        self,
        symbol: str,
        shares: float,
        price: float,
        transaction_date: Optional[date] = None,
        fees: float = 0,
        account: str = "default",
        notes: str = ""
    ) -> int:
        """
        Record a stock purchase.

        Args:
            symbol: Stock symbol
            shares: Number of shares purchased
            price: Price per share
            transaction_date: Date of purchase (default: today)
            fees: Transaction fees
            account: Account name/identifier
            notes: Optional notes

        Returns:
            Transaction ID
        """
        if transaction_date is None:
            transaction_date = date.today()

        symbol = symbol.upper()
        total_amount = (shares * price) + fees

        # Record transaction
        transaction_data = {
            "symbol": symbol,
            "transaction_type": "BUY",
            "shares": shares,
            "price": price,
            "total_amount": total_amount,
            "fees": fees,
            "transaction_date": transaction_date.isoformat(),
            "account": account,
            "notes": notes,
        }
        transaction_id = self.db.insert(self.TRANSACTIONS_TABLE, transaction_data)

        # Update or create holding
        existing = self.db.fetchone(
            f"SELECT * FROM {self.HOLDINGS_TABLE} WHERE symbol = ? AND account = ?",
            (symbol, account)
        )

        if existing:
            # Average down/up the cost basis
            total_shares = existing["shares"] + shares
            total_cost = (existing["shares"] * existing["cost_basis"]) + (shares * price)
            new_cost_basis = total_cost / total_shares

            self.db.update(
                self.HOLDINGS_TABLE,
                {"shares": total_shares, "cost_basis": new_cost_basis},
                "id = ?",
                (existing["id"],)
            )
        else:
            # Create new holding
            holding_data = {
                "symbol": symbol,
                "shares": shares,
                "cost_basis": price,
                "purchase_date": transaction_date.isoformat(),
                "account": account,
                "notes": notes,
            }
            self.db.insert(self.HOLDINGS_TABLE, holding_data)

        return transaction_id

    def sell(
        self,
        symbol: str,
        shares: float,
        price: float,
        transaction_date: Optional[date] = None,
        fees: float = 0,
        account: str = "default",
        notes: str = ""
    ) -> Optional[int]:
        """
        Record a stock sale.

        Returns:
            Transaction ID or None if insufficient shares
        """
        if transaction_date is None:
            transaction_date = date.today()

        symbol = symbol.upper()

        # Check if we have enough shares
        holding = self.db.fetchone(
            f"SELECT * FROM {self.HOLDINGS_TABLE} WHERE symbol = ? AND account = ?",
            (symbol, account)
        )

        if not holding or holding["shares"] < shares:
            return None

        total_amount = (shares * price) - fees

        # Record transaction
        transaction_data = {
            "symbol": symbol,
            "transaction_type": "SELL",
            "shares": shares,
            "price": price,
            "total_amount": total_amount,
            "fees": fees,
            "transaction_date": transaction_date.isoformat(),
            "account": account,
            "notes": notes,
        }
        transaction_id = self.db.insert(self.TRANSACTIONS_TABLE, transaction_data)

        # Update holding
        remaining_shares = holding["shares"] - shares
        if remaining_shares <= 0:
            self.db.delete(self.HOLDINGS_TABLE, "id = ?", (holding["id"],))
        else:
            self.db.update(
                self.HOLDINGS_TABLE,
                {"shares": remaining_shares},
                "id = ?",
                (holding["id"],)
            )

        return transaction_id

    def get_holdings(self, account: Optional[str] = None) -> list[dict]:
        """Get all current holdings."""
        if account:
            rows = self.db.fetchall(
                f"SELECT * FROM {self.HOLDINGS_TABLE} WHERE account = ? ORDER BY symbol",
                (account,)
            )
        else:
            rows = self.db.fetchall(
                f"SELECT * FROM {self.HOLDINGS_TABLE} ORDER BY account, symbol"
            )

        holdings = []
        for row in rows:
            holding = dict(row)

            # Get current price
            latest = self.stock_analyzer.get_latest_price(holding["symbol"])
            if latest:
                holding["current_price"] = latest["close"]
                holding["price_date"] = latest["date"]
                holding["market_value"] = holding["shares"] * latest["close"]
                holding["total_cost"] = holding["shares"] * holding["cost_basis"]
                holding["gain_loss"] = holding["market_value"] - holding["total_cost"]
                holding["gain_loss_percent"] = (holding["gain_loss"] / holding["total_cost"]) * 100

            holdings.append(holding)

        return holdings

    def get_holding(self, symbol: str, account: str = "default") -> Optional[dict]:
        """Get a specific holding."""
        row = self.db.fetchone(
            f"SELECT * FROM {self.HOLDINGS_TABLE} WHERE symbol = ? AND account = ?",
            (symbol.upper(), account)
        )
        return dict(row) if row else None

    def get_transactions(
        self,
        symbol: Optional[str] = None,
        account: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """Get transaction history."""
        conditions = []
        params = []

        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol.upper())

        if account:
            conditions.append("account = ?")
            params.append(account)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        rows = self.db.fetchall(
            f"""SELECT * FROM {self.TRANSACTIONS_TABLE}
                WHERE {where_clause}
                ORDER BY transaction_date DESC, created_at DESC
                LIMIT ?""",
            tuple(params)
        )
        return [dict(row) for row in rows]

    def get_portfolio_summary(self, account: Optional[str] = None) -> dict:
        """Get portfolio summary with totals."""
        holdings = self.get_holdings(account)

        total_cost = 0
        total_value = 0
        total_gain_loss = 0

        for h in holdings:
            if "total_cost" in h:
                total_cost += h["total_cost"]
            if "market_value" in h:
                total_value += h["market_value"]
            if "gain_loss" in h:
                total_gain_loss += h["gain_loss"]

        return {
            "account": account or "all",
            "holdings_count": len(holdings),
            "total_cost": total_cost,
            "total_value": total_value,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_percent": (total_gain_loss / total_cost * 100) if total_cost > 0 else 0,
            "holdings": holdings,
        }

    def get_allocation(self, account: Optional[str] = None) -> list[dict]:
        """Get portfolio allocation by symbol."""
        holdings = self.get_holdings(account)
        total_value = sum(h.get("market_value", 0) for h in holdings)

        allocation = []
        for h in holdings:
            market_value = h.get("market_value", 0)
            allocation.append({
                "symbol": h["symbol"],
                "shares": h["shares"],
                "market_value": market_value,
                "percentage": (market_value / total_value * 100) if total_value > 0 else 0,
            })

        return sorted(allocation, key=lambda x: x["percentage"], reverse=True)

    def get_realized_gains(
        self,
        year: Optional[int] = None,
        account: Optional[str] = None
    ) -> dict:
        """Calculate realized gains from sales."""
        conditions = ["transaction_type = 'SELL'"]
        params = []

        if year:
            conditions.append("strftime('%Y', transaction_date) = ?")
            params.append(str(year))

        if account:
            conditions.append("account = ?")
            params.append(account)

        where_clause = " AND ".join(conditions)

        # This is simplified - proper implementation would track lots
        rows = self.db.fetchall(
            f"SELECT * FROM {self.TRANSACTIONS_TABLE} WHERE {where_clause}",
            tuple(params)
        )

        total_proceeds = sum(row["total_amount"] for row in rows)
        total_fees = sum(row["fees"] for row in rows)

        return {
            "year": year or "all",
            "account": account or "all",
            "total_sales": len(rows),
            "total_proceeds": total_proceeds,
            "total_fees": total_fees,
        }

    def get_accounts(self) -> list[str]:
        """Get list of all account names."""
        rows = self.db.fetchall(
            f"SELECT DISTINCT account FROM {self.HOLDINGS_TABLE} ORDER BY account"
        )
        return [row["account"] for row in rows]
