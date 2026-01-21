"""
Rendering helpers for CV/resume entries.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable

from modules.core.utils import parse_date

SECTION_LABELS = {
    "experience": "WORK EXPERIENCE",
    "education": "EDUCATION",
    "skill": "SKILLS",
    "project": "PROJECTS",
    "certification": "CERTIFICATIONS",
}


def render_text(entries: Iterable[dict]) -> str:
    """Render entries as a plain-text CV."""
    sections = _group_entries(entries)
    output = ["=" * 50, "CURRICULUM VITAE", "=" * 50, ""]

    for label, items in sections:
        if not items:
            continue
        output.append(f"\n{label}")
        output.append("-" * len(label))
        for item in items:
            output.extend(_format_text_entry(item))

    return "\n".join(output).strip() + "\n"


def render_markdown(entries: Iterable[dict]) -> str:
    """Render entries as markdown."""
    sections = _group_entries(entries)
    output = ["# Curriculum Vitae", ""]

    for label, items in sections:
        if not items:
            continue
        output.append(f"## {label.title()}")
        output.append("")
        for item in items:
            output.extend(_format_markdown_entry(item))
            output.append("")

    return "\n".join(output).strip() + "\n"


def _group_entries(entries: Iterable[dict]) -> list[tuple[str, list[dict]]]:
    grouped = {key: [] for key in SECTION_LABELS}
    for entry in entries:
        entry_type = entry.get("entry_type")
        if entry_type in grouped:
            grouped[entry_type].append(entry)

    ordered = []
    for key, label in SECTION_LABELS.items():
        items = sorted(grouped[key], key=_entry_sort_key, reverse=True)
        ordered.append((label, items))
    return ordered


def _entry_sort_key(entry: dict) -> date:
    for field in ("end_date", "start_date"):
        value = entry.get(field)
        if value:
            try:
                return parse_date(value)
            except ValueError:
                continue
    return date.min


def _format_text_entry(item: dict) -> list[str]:
    lines = []
    org = f" @ {item['organization']}" if item.get("organization") else ""
    dates = _format_dates(item.get("start_date"), item.get("end_date"))
    lines.append(f"  • {item['title']}{org}{dates}")
    if item.get("description"):
        lines.append(f"    {item['description']}")
    lines.extend(_format_highlights(item.get("highlights"), prefix="    - "))
    return lines


def _format_markdown_entry(item: dict) -> list[str]:
    lines = []
    org = f" @ {item['organization']}" if item.get("organization") else ""
    dates = _format_dates(item.get("start_date"), item.get("end_date"))
    lines.append(f"- **{item['title']}**{org}{dates}")
    if item.get("description"):
        lines.append(f"  - {item['description']}")
    lines.extend(_format_highlights(item.get("highlights"), prefix="  - "))
    return lines


def _format_dates(start_date: str | None, end_date: str | None) -> str:
    if not start_date and not end_date:
        return ""
    if start_date and not end_date:
        return f" ({start_date} - present)"
    if not start_date and end_date:
        return f" (until {end_date})"
    return f" ({start_date} - {end_date})"


def _format_highlights(highlights: str | None, prefix: str) -> list[str]:
    if not highlights:
        return []
    items = [line.strip() for line in highlights.splitlines() if line.strip()]
    return [f"{prefix}{item}" for item in items]
