"""
Atlas Personal OS - Slack Notifier

Send progress updates to Slack via webhook.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from datetime import datetime


class SlackNotifier:
    """Send notifications to Slack."""

    def __init__(self, webhook_url: str):
        """
        Initialize with Slack webhook URL.

        Args:
            webhook_url: Slack incoming webhook URL
        """
        self.webhook_url = webhook_url

    def send(self, message: str) -> bool:
        """
        Send a message to Slack.

        Args:
            message: Message text (supports Slack markdown)

        Returns:
            True if sent successfully
        """
        try:
            data = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except urllib.error.URLError:
            return False

    def send_progress_update(
        self,
        completed: list[str],
        in_progress: list[str],
        next_steps: list[str],
        stats: Optional[dict] = None
    ) -> bool:
        """
        Send a formatted progress update.

        Args:
            completed: List of completed items
            in_progress: List of in-progress items
            next_steps: List of next steps
            stats: Optional stats dict (e.g., {"tests": 77, "features": "7/28"})
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"*Atlas Personal OS - Progress Update*",
            f"_{timestamp}_",
            ""
        ]

        if completed:
            lines.append(":white_check_mark: *Completed:*")
            for item in completed:
                lines.append(f"• {item}")
            lines.append("")

        if in_progress:
            lines.append(":hourglass_flowing_sand: *In Progress:*")
            for item in in_progress:
                lines.append(f"• {item}")
            lines.append("")

        if next_steps:
            lines.append(":arrow_right: *Next Steps:*")
            for item in next_steps:
                lines.append(f"• {item}")
            lines.append("")

        if stats:
            lines.append(":bar_chart: *Stats:*")
            for key, value in stats.items():
                lines.append(f"• {key}: {value}")

        return self.send("\n".join(lines))

    def send_error(self, error: str, context: str = "") -> bool:
        """Send an error notification."""
        message = f":x: *Error in Atlas Personal OS*\n\n{error}"
        if context:
            message += f"\n\n_Context: {context}_"
        return self.send(message)

    def send_success(self, message: str) -> bool:
        """Send a success notification."""
        return self.send(f":white_check_mark: {message}")


# Default webhook URL (can be overridden)
DEFAULT_WEBHOOK_URL = "https://hooks.slack.com/services/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"

_default_notifier: Optional[SlackNotifier] = None


def get_notifier() -> SlackNotifier:
    """Get the default Slack notifier."""
    global _default_notifier
    if _default_notifier is None:
        _default_notifier = SlackNotifier(DEFAULT_WEBHOOK_URL)
    return _default_notifier


def notify(message: str) -> bool:
    """Quick function to send a Slack notification."""
    return get_notifier().send(message)
