"""
Atlas Personal OS - Common Utilities

Shared helper functions used across all modules.
"""

from datetime import datetime, date
from typing import Optional, Any
import re


def format_date(d: date | datetime | str, fmt: str = "%Y-%m-%d") -> str:
    """
    Format a date to string.

    Args:
        d: Date object or string
        fmt: Output format string

    Returns:
        Formatted date string
    """
    if isinstance(d, str):
        d = parse_date(d)
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime(fmt)


def parse_date(date_str: str) -> date:
    """
    Parse a date string in various formats.

    Args:
        date_str: Date string (supports YYYY-MM-DD, MM/DD/YYYY, etc.)

    Returns:
        Date object
    """
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")


def format_datetime(dt: datetime | str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime to string.

    Args:
        dt: Datetime object or string
        fmt: Output format string

    Returns:
        Formatted datetime string
    """
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt.strftime(fmt)


def parse_datetime(dt_str: str) -> datetime:
    """
    Parse a datetime string.

    Args:
        dt_str: Datetime string

    Returns:
        Datetime object
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse datetime: {dt_str}")


def days_since(d: date | datetime | str) -> int:
    """
    Calculate days since a given date.

    Args:
        d: Date to calculate from

    Returns:
        Number of days since the date
    """
    if isinstance(d, str):
        d = parse_date(d)
    if isinstance(d, datetime):
        d = d.date()
    return (date.today() - d).days


def days_until(d: date | datetime | str) -> int:
    """
    Calculate days until a given date.

    Args:
        d: Date to calculate to

    Returns:
        Number of days until the date (negative if in past)
    """
    if isinstance(d, str):
        d = parse_date(d)
    if isinstance(d, datetime):
        d = d.date()
    return (d - date.today()).days


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to convert

    Returns:
        Slugified text
    """
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def truncate(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def validate_email(email: str) -> bool:
    """
    Validate an email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid format, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def safe_get(data: dict | list, *keys: Any, default: Any = None) -> Any:
    """
    Safely get nested value from dict/list.

    Args:
        data: Dictionary or list
        *keys: Keys/indices to traverse
        default: Default value if not found

    Returns:
        Value at nested path or default
    """
    for key in keys:
        try:
            data = data[key]
        except (KeyError, IndexError, TypeError):
            return default
    return data


def format_currency(amount: float, currency: str = "USD", symbol: str = "$") -> str:
    """
    Format a number as currency.

    Args:
        amount: Amount to format
        currency: Currency code (for future use)
        symbol: Currency symbol

    Returns:
        Formatted currency string
    """
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a number as percentage.

    Args:
        value: Value to format (0.15 = 15%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"
