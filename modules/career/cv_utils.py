"""
Utility helpers for CV/resume entries.
"""

from __future__ import annotations

from typing import Iterable

from modules.core.utils import parse_date


def normalize_date(value: str) -> str:
    """Normalize a date string to YYYY-MM-DD or return empty."""
    if not value:
        return ""
    return parse_date(value).isoformat()


def normalize_tags(tags: str | Iterable[str]) -> str:
    """Normalize tags into a comma-separated string."""
    if not tags:
        return ""
    if isinstance(tags, str):
        items = [tag.strip() for tag in tags.split(",") if tag.strip()]
    else:
        items = [tag.strip() for tag in tags if tag.strip()]

    seen = set()
    ordered = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)

    return ", ".join(ordered)


def normalize_highlights(highlights: str | Iterable[str]) -> str:
    """Normalize highlights into a newline-delimited string."""
    if not highlights:
        return ""
    if isinstance(highlights, str):
        return highlights.strip()
    return "\n".join(item.strip() for item in highlights if item.strip())


def parse_tags(tags: str) -> list[str]:
    """Split a tag string into a list."""
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def matches_query(entry: dict, query: str) -> bool:
    """Check if a query matches common entry fields."""
    haystack = " ".join([
        entry.get("title", ""),
        entry.get("organization", ""),
        entry.get("description", ""),
        entry.get("tags", ""),
        entry.get("highlights", ""),
    ]).lower()
    return query.lower() in haystack


def is_within_date_range(entry: dict, start_after: str | None, end_before: str | None) -> bool:
    """Check if entry falls within the provided date range."""
    if not start_after and not end_before:
        return True

    entry_start = entry.get("start_date") or ""
    entry_end = entry.get("end_date") or entry_start

    if start_after:
        start_after = normalize_date(start_after)
        if entry_end and entry_end < start_after:
            return False

    if end_before:
        end_before = normalize_date(end_before)
        if entry_start and entry_start > end_before:
            return False

    return True
