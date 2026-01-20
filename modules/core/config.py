"""
Atlas Personal OS - Configuration Manager

Manages user settings stored in YAML/JSON configuration files.
All config files are stored in the config/ directory.
"""

import json
from pathlib import Path
from typing import Any, Optional


class Config:
    """Configuration manager for Atlas Personal OS."""

    def __init__(self, config_name: str = "settings.json", config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_name: Configuration filename (default: settings.json)
            config_dir: Directory for config files (default: project/config/)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"

        config_dir.mkdir(exist_ok=True)
        self.config_path = config_dir / config_name
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._data = json.load(f)
        else:
            self._data = self._get_defaults()
            self._save()

    def _save(self) -> None:
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def _get_defaults(self) -> dict[str, Any]:
        """Get default configuration values."""
        return {
            "app": {
                "name": "Atlas Personal OS",
                "version": "0.1.0",
                "debug": False
            },
            "database": {
                "name": "atlas.db"
            },
            "user": {
                "name": "",
                "email": ""
            },
            "modules": {
                "finance": {"enabled": True},
                "career": {"enabled": True},
                "content": {"enabled": True},
                "life": {"enabled": True},
                "knowledge": {"enabled": True}
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "app.name" or "user.email")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "user.name")
            value: Value to set
        """
        keys = key.split(".")
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value
        self._save()

    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.

        Args:
            key: Configuration key to delete

        Returns:
            True if key was deleted, False if not found
        """
        keys = key.split(".")
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                return False
            data = data[k]

        if keys[-1] in data:
            del data[keys[-1]]
            self._save()
            return True
        return False

    def all(self) -> dict[str, Any]:
        """Get all configuration data."""
        return self._data.copy()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._data = self._get_defaults()
        self._save()

    def section(self, name: str) -> dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            name: Section name (e.g., "app", "user", "modules")

        Returns:
            Section data as dictionary
        """
        return self._data.get(name, {}).copy()


# Singleton instance
_default_config: Optional[Config] = None


def get_config() -> Config:
    """Get the default configuration instance."""
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config
