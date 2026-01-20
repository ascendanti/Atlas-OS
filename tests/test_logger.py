# Tests for CORE-004 Logging System

import json
import os
import tempfile
from pathlib import Path

import pytest

from modules.core.logger import Logger, LogLevel, get_logger, log, LEVEL_MAP


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_level_ordering(self):
        """Log levels should be ordered by severity."""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR

    def test_level_map_contains_all_levels(self):
        """LEVEL_MAP should contain all LogLevel values."""
        for level in LogLevel:
            assert level.name in LEVEL_MAP
            assert LEVEL_MAP[level.name] == level


class TestLoggerBasics:
    """Basic logger functionality tests."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return tmp_path / "test.log"

    @pytest.fixture
    def logger(self, temp_log_file):
        """Create a logger with temp file."""
        return Logger(log_path=str(temp_log_file), min_level=LogLevel.DEBUG)

    def test_logger_creates_directory(self, tmp_path):
        """Logger should create log directory if it doesn't exist."""
        log_path = tmp_path / "nested" / "dir" / "test.log"
        logger = Logger(log_path=str(log_path))
        assert log_path.parent.exists()

    def test_logger_default_level(self, temp_log_file):
        """Logger should default to INFO level."""
        logger = Logger(log_path=str(temp_log_file))
        assert logger.min_level == LogLevel.INFO

    def test_logger_string_level(self, temp_log_file):
        """Logger should accept string level."""
        logger = Logger(log_path=str(temp_log_file), min_level="WARNING")
        assert logger.min_level == LogLevel.WARNING

    def test_logger_case_insensitive_level(self, temp_log_file):
        """Logger should handle case-insensitive level strings."""
        logger = Logger(log_path=str(temp_log_file), min_level="error")
        assert logger.min_level == LogLevel.ERROR


class TestLogging:
    """Tests for actual logging functionality."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return tmp_path / "test.log"

    @pytest.fixture
    def logger(self, temp_log_file):
        """Create a logger with temp file."""
        return Logger(log_path=str(temp_log_file), min_level=LogLevel.DEBUG)

    def test_log_creates_file(self, logger, temp_log_file):
        """Logging should create the log file."""
        logger.info("Test message")
        assert temp_log_file.exists()

    def test_log_jsonl_format(self, logger, temp_log_file):
        """Log entries should be valid JSON."""
        logger.info("Test message")
        with open(temp_log_file) as f:
            line = f.readline()
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "level" in entry
        assert "module" in entry
        assert "message" in entry

    def test_log_contains_message(self, logger, temp_log_file):
        """Log entry should contain the message."""
        logger.info("Hello World")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["message"] == "Hello World"

    def test_log_contains_level(self, logger, temp_log_file):
        """Log entry should contain the level name."""
        logger.warning("Warning message")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["level"] == "WARNING"

    def test_log_contains_module(self, logger, temp_log_file):
        """Log entry should contain module name."""
        logger.info("Test", module="test_module")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["module"] == "test_module"

    def test_log_default_module(self, temp_log_file):
        """Log entry should use default module name."""
        logger = Logger(log_path=str(temp_log_file), module_name="my_module")
        logger.info("Test")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["module"] == "my_module"

    def test_log_with_context(self, logger, temp_log_file):
        """Log entry should include context."""
        logger.info("Test", context={"user_id": 123, "action": "login"})
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["context"]["user_id"] == 123
        assert entry["context"]["action"] == "login"


class TestLogLevelFiltering:
    """Tests for log level filtering."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return tmp_path / "test.log"

    def test_filters_below_min_level(self, temp_log_file):
        """Logger should filter entries below min level."""
        logger = Logger(log_path=str(temp_log_file), min_level=LogLevel.WARNING)
        result = logger.debug("Should not log")
        assert result is False
        assert not temp_log_file.exists()

    def test_logs_at_min_level(self, temp_log_file):
        """Logger should log entries at min level."""
        logger = Logger(log_path=str(temp_log_file), min_level=LogLevel.WARNING)
        result = logger.warning("Should log")
        assert result is True
        assert temp_log_file.exists()

    def test_logs_above_min_level(self, temp_log_file):
        """Logger should log entries above min level."""
        logger = Logger(log_path=str(temp_log_file), min_level=LogLevel.WARNING)
        result = logger.error("Should log")
        assert result is True
        assert temp_log_file.exists()

    def test_info_filtered_when_min_warning(self, temp_log_file):
        """INFO should be filtered when min level is WARNING."""
        logger = Logger(log_path=str(temp_log_file), min_level=LogLevel.WARNING)
        logger.info("Should not log")
        logger.warning("Should log")
        with open(temp_log_file) as f:
            lines = f.readlines()
        assert len(lines) == 1
        assert "Should log" in lines[0]


class TestSensitiveDataFiltering:
    """Tests for sensitive data filtering in context."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return tmp_path / "test.log"

    @pytest.fixture
    def logger(self, temp_log_file):
        """Create a logger with temp file."""
        return Logger(log_path=str(temp_log_file), min_level=LogLevel.DEBUG)

    def test_filters_password(self, logger, temp_log_file):
        """Logger should filter password from context."""
        logger.info("Login", context={"user": "alice", "password": "secret123"})
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert "password" not in entry.get("context", {})
        assert entry["context"]["user"] == "alice"

    def test_filters_token(self, logger, temp_log_file):
        """Logger should filter token from context."""
        logger.info("API call", context={"endpoint": "/api", "token": "abc123"})
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert "token" not in entry.get("context", {})

    def test_filters_api_key(self, logger, temp_log_file):
        """Logger should filter api_key from context."""
        logger.info("Request", context={"api_key": "key123", "data": "test"})
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert "api_key" not in entry.get("context", {})

    def test_filters_webhook(self, logger, temp_log_file):
        """Logger should filter webhook from context."""
        logger.info("Notification", context={"webhook": "https://...", "channel": "#general"})
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert "webhook" not in entry.get("context", {})


class TestConvenienceMethods:
    """Tests for convenience logging methods."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return tmp_path / "test.log"

    @pytest.fixture
    def logger(self, temp_log_file):
        """Create a logger with temp file."""
        return Logger(log_path=str(temp_log_file), min_level=LogLevel.DEBUG)

    def test_debug_method(self, logger, temp_log_file):
        """debug() should log at DEBUG level."""
        logger.debug("Debug message")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["level"] == "DEBUG"

    def test_info_method(self, logger, temp_log_file):
        """info() should log at INFO level."""
        logger.info("Info message")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["level"] == "INFO"

    def test_warning_method(self, logger, temp_log_file):
        """warning() should log at WARNING level."""
        logger.warning("Warning message")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["level"] == "WARNING"

    def test_error_method(self, logger, temp_log_file):
        """error() should log at ERROR level."""
        logger.error("Error message")
        with open(temp_log_file) as f:
            entry = json.loads(f.readline())
        assert entry["level"] == "ERROR"


class TestReadLogs:
    """Tests for reading log entries."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return tmp_path / "test.log"

    @pytest.fixture
    def logger(self, temp_log_file):
        """Create a logger with temp file."""
        return Logger(log_path=str(temp_log_file), min_level=LogLevel.DEBUG)

    def test_read_empty_log(self, logger, temp_log_file):
        """Reading non-existent log should return empty list."""
        entries = logger.read_logs()
        assert entries == []

    def test_read_logs_returns_entries(self, logger, temp_log_file):
        """read_logs should return logged entries."""
        logger.info("First")
        logger.info("Second")
        entries = logger.read_logs()
        assert len(entries) == 2
        assert entries[0]["message"] == "First"
        assert entries[1]["message"] == "Second"

    def test_read_logs_limit(self, logger, temp_log_file):
        """read_logs should respect limit parameter."""
        for i in range(10):
            logger.info(f"Message {i}")
        entries = logger.read_logs(limit=3)
        assert len(entries) == 3
        # Should return most recent
        assert entries[0]["message"] == "Message 7"
        assert entries[2]["message"] == "Message 9"

    def test_read_logs_level_filter(self, logger, temp_log_file):
        """read_logs should filter by level."""
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        entries = logger.read_logs(level_filter=LogLevel.WARNING)
        assert len(entries) == 2
        levels = [e["level"] for e in entries]
        assert "DEBUG" not in levels
        assert "INFO" not in levels


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_logger_returns_logger(self, tmp_path):
        """get_logger should return a Logger instance."""
        log_path = tmp_path / "test.log"
        logger = get_logger(log_path=str(log_path))
        assert isinstance(logger, Logger)

    def test_log_function(self, tmp_path):
        """log() convenience function should work."""
        log_path = tmp_path / "test.log"
        get_logger(log_path=str(log_path), min_level=LogLevel.DEBUG)
        result = log(LogLevel.INFO, "test_module", "Test message")
        assert result is True
        with open(log_path) as f:
            entry = json.loads(f.readline())
        assert entry["message"] == "Test message"
        assert entry["module"] == "test_module"
