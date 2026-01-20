# Atlas Personal OS - Structured Logger
# CORE-004: JSONL logging with levels, timestamps, and context

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any


class LogLevel(IntEnum):
    """Log levels in order of severity."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


# String to level mapping
LEVEL_MAP = {
    "DEBUG": LogLevel.DEBUG,
    "INFO": LogLevel.INFO,
    "WARNING": LogLevel.WARNING,
    "ERROR": LogLevel.ERROR,
}


class Logger:
    """Structured JSONL logger for Atlas Personal OS.

    Writes log entries as JSON lines to a configurable file path.
    Supports log level filtering and optional context data.
    """

    DEFAULT_LOG_PATH = "data/logs/atlas.log"
    DEFAULT_LEVEL = LogLevel.INFO

    def __init__(
        self,
        log_path: str | None = None,
        min_level: LogLevel | str = DEFAULT_LEVEL,
        module_name: str = "atlas",
    ):
        """Initialize logger.

        Args:
            log_path: Path to log file. Defaults to data/logs/atlas.log
            min_level: Minimum log level to record. Can be LogLevel or string.
            module_name: Default module name for log entries.
        """
        self.log_path = Path(log_path) if log_path else Path(self.DEFAULT_LOG_PATH)
        self.module_name = module_name

        # Convert string level to LogLevel if needed
        if isinstance(min_level, str):
            self.min_level = LEVEL_MAP.get(min_level.upper(), self.DEFAULT_LEVEL)
        else:
            self.min_level = min_level

        # Ensure log directory exists
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Create log directory if it doesn't exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _format_entry(
        self,
        level: LogLevel,
        message: str,
        module: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Format a log entry as JSON.

        Args:
            level: Log level
            message: Log message
            module: Module name (uses default if not provided)
            context: Optional context dictionary

        Returns:
            JSON string (single line)
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.name,
            "module": module or self.module_name,
            "message": message,
        }

        if context:
            # Filter out sensitive keys and ensure JSON-serializable
            safe_context = self._sanitize_context(context)
            if safe_context:
                entry["context"] = safe_context

        return json.dumps(entry, default=str)

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive keys from context.

        Args:
            context: Raw context dictionary

        Returns:
            Sanitized context dictionary
        """
        sensitive_keys = {"password", "token", "secret", "api_key", "webhook"}
        return {
            k: v for k, v in context.items()
            if k.lower() not in sensitive_keys
        }

    def _write(self, entry: str) -> None:
        """Write a log entry to file.

        Args:
            entry: JSON log entry string
        """
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def log(
        self,
        level: LogLevel | str,
        message: str,
        module: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Write a log entry if level meets minimum threshold.

        Args:
            level: Log level (LogLevel enum or string)
            message: Log message
            module: Optional module name override
            context: Optional context dictionary

        Returns:
            True if logged, False if filtered
        """
        # Convert string level to LogLevel
        if isinstance(level, str):
            level = LEVEL_MAP.get(level.upper(), LogLevel.INFO)

        # Check against minimum level
        if level < self.min_level:
            return False

        entry = self._format_entry(level, message, module, context)
        self._write(entry)
        return True

    def debug(self, message: str, module: str | None = None, context: dict[str, Any] | None = None) -> bool:
        """Log a DEBUG message."""
        return self.log(LogLevel.DEBUG, message, module, context)

    def info(self, message: str, module: str | None = None, context: dict[str, Any] | None = None) -> bool:
        """Log an INFO message."""
        return self.log(LogLevel.INFO, message, module, context)

    def warning(self, message: str, module: str | None = None, context: dict[str, Any] | None = None) -> bool:
        """Log a WARNING message."""
        return self.log(LogLevel.WARNING, message, module, context)

    def error(self, message: str, module: str | None = None, context: dict[str, Any] | None = None) -> bool:
        """Log an ERROR message."""
        return self.log(LogLevel.ERROR, message, module, context)

    def read_logs(self, limit: int = 100, level_filter: LogLevel | str | None = None) -> list[dict]:
        """Read recent log entries.

        Args:
            limit: Maximum entries to return
            level_filter: Optional level to filter by (and above)

        Returns:
            List of log entry dictionaries
        """
        if not self.log_path.exists():
            return []

        # Convert string filter to LogLevel
        if isinstance(level_filter, str):
            level_filter = LEVEL_MAP.get(level_filter.upper())

        entries = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Apply level filter if provided
                    if level_filter:
                        entry_level = LEVEL_MAP.get(entry.get("level", "INFO"), LogLevel.INFO)
                        if entry_level < level_filter:
                            continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        # Return most recent entries
        return entries[-limit:]


# Module-level convenience instance
_default_logger: Logger | None = None


def get_logger(
    log_path: str | None = None,
    min_level: LogLevel | str = LogLevel.INFO,
    module_name: str = "atlas",
) -> Logger:
    """Get or create a logger instance.

    Args:
        log_path: Path to log file
        min_level: Minimum log level
        module_name: Default module name

    Returns:
        Logger instance
    """
    global _default_logger
    if _default_logger is None or log_path is not None:
        _default_logger = Logger(log_path, min_level, module_name)
    return _default_logger


def log(
    level: LogLevel | str,
    module: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> bool:
    """Convenience function to log using default logger.

    Args:
        level: Log level
        module: Module name
        message: Log message
        context: Optional context

    Returns:
        True if logged
    """
    logger = get_logger()
    return logger.log(level, message, module, context)
