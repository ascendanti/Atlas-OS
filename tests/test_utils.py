"""
Tests for the Utils module.
"""

import pytest
from datetime import date, datetime

from modules.core.utils import (
    format_date, parse_date, format_datetime, parse_datetime,
    days_since, days_until, slugify, truncate, validate_email,
    safe_get, format_currency, format_percentage
)


class TestDateUtils:
    """Tests for date utility functions."""

    def test_format_date_from_date(self):
        """Test formatting a date object."""
        d = date(2024, 1, 15)
        assert format_date(d) == "2024-01-15"

    def test_format_date_from_string(self):
        """Test formatting from a string."""
        assert format_date("2024-01-15") == "2024-01-15"

    def test_format_date_custom_format(self):
        """Test custom date format."""
        d = date(2024, 1, 15)
        assert format_date(d, "%m/%d/%Y") == "01/15/2024"

    def test_parse_date_iso(self):
        """Test parsing ISO date format."""
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_date_us_format(self):
        """Test parsing US date format."""
        result = parse_date("01/15/2024")
        assert result == date(2024, 1, 15)

    def test_parse_date_invalid(self):
        """Test parsing invalid date raises error."""
        with pytest.raises(ValueError):
            parse_date("not-a-date")

    def test_format_datetime(self):
        """Test formatting datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        assert format_datetime(dt) == "2024-01-15 10:30:45"

    def test_parse_datetime(self):
        """Test parsing datetime string."""
        result = parse_datetime("2024-01-15 10:30:45")
        assert result == datetime(2024, 1, 15, 10, 30, 45)

    def test_days_since(self):
        """Test calculating days since a date."""
        past_date = date.today() - date.resolution * 10
        # This will be approximately 10 days
        result = days_since(past_date)
        assert result >= 0

    def test_days_until(self):
        """Test calculating days until a date."""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=10)
        result = days_until(future_date)
        assert result == 10


class TestStringUtils:
    """Tests for string utility functions."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello-world"

    def test_slugify_special_chars(self):
        """Test slugify removes special characters."""
        assert slugify("Hello! World?") == "hello-world"

    def test_slugify_multiple_spaces(self):
        """Test slugify handles multiple spaces."""
        assert slugify("Hello   World") == "hello-world"

    def test_truncate_short_string(self):
        """Test truncate doesn't change short strings."""
        assert truncate("Short", max_length=10) == "Short"

    def test_truncate_long_string(self):
        """Test truncate shortens long strings."""
        result = truncate("This is a very long string", max_length=15)
        assert result == "This is a ve..."
        assert len(result) == 15

    def test_truncate_custom_suffix(self):
        """Test truncate with custom suffix."""
        result = truncate("Long text here", max_length=10, suffix="~")
        assert result.endswith("~")


class TestValidation:
    """Tests for validation functions."""

    def test_validate_email_valid(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
        assert validate_email("user+tag@example.org") is True

    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        assert validate_email("not-an-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("") is False


class TestDataHelpers:
    """Tests for data helper functions."""

    def test_safe_get_dict(self):
        """Test safe_get with dictionaries."""
        data = {"a": {"b": {"c": 123}}}
        assert safe_get(data, "a", "b", "c") == 123
        assert safe_get(data, "a", "b", "d", default=None) is None
        assert safe_get(data, "x", "y", default="default") == "default"

    def test_safe_get_list(self):
        """Test safe_get with lists."""
        data = [1, 2, [3, 4, 5]]
        assert safe_get(data, 2, 1) == 4
        assert safe_get(data, 10, default=None) is None

    def test_safe_get_mixed(self):
        """Test safe_get with mixed data."""
        data = {"items": [{"name": "first"}, {"name": "second"}]}
        assert safe_get(data, "items", 0, "name") == "first"
        assert safe_get(data, "items", 5, "name", default="not found") == "not found"


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_currency_positive(self):
        """Test formatting positive currency."""
        assert format_currency(1234.56) == "$1,234.56"

    def test_format_currency_negative(self):
        """Test formatting negative currency."""
        assert format_currency(-1234.56) == "-$1,234.56"

    def test_format_currency_zero(self):
        """Test formatting zero."""
        assert format_currency(0) == "$0.00"

    def test_format_percentage(self):
        """Test formatting percentages."""
        assert format_percentage(0.15) == "15.00%"
        assert format_percentage(0.5) == "50.00%"
        assert format_percentage(1.0) == "100.00%"

    def test_format_percentage_decimals(self):
        """Test percentage with custom decimals."""
        assert format_percentage(0.1234, decimals=1) == "12.3%"
        assert format_percentage(0.1234, decimals=0) == "12%"
