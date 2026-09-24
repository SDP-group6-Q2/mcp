"""Markdown helpers shared by the domains' formatters. Pure functions, no I/O."""

from collections.abc import Sequence
from typing import Any


def cell(value: Any) -> str:
    """One table cell: missing values are shown explicitly, and text can't break the table."""
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(rows: Sequence[dict[str, Any]], columns: Sequence[tuple[str, str]]) -> str:
    """Markdown table. `columns` are (header, key) pairs."""
    header = "| " + " | ".join(title for title, _ in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(cell(row.get(key)) for _, key in columns) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def bullets(fields: Sequence[tuple[str, Any]]) -> str:
    """'- **Label:** value' lines, with missing values shown explicitly."""
    return "\n".join(f"- **{label}:** {cell(value)}" for label, value in fields)


def page_note(page: dict[str, Any]) -> str:
    """A footer telling the model whether a paged result is complete and how to get more."""
    if not page.get("truncated"):
        return ""
    return (
        f"\n\nShowing {page['returned_count']} rows; more exist. "
        f"To continue, call again with cursor={page['next_cursor']!r}."
    )
