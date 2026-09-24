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


def short_ts(value: Any) -> str | None:
    """'2026-07-06T14:21:00' -> '2026-07-06 14:21'; a plain date is returned as is."""
    if value is None:
        return None
    text = str(value)
    return text.replace("T", " ")[:16] if "T" in text else text


def num(value: Any, digits: int = 1) -> str | None:
    """Round a number for display, dropping trailing zeros ('91.60' -> '91.6', '26104.3' -> '26104.3')."""
    if value is None:
        return None
    text = f"{round(float(value), digits):.{digits}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def page_header(page: dict[str, Any], what: str, order: str) -> str:
    """'Showing 12 <what> (<order>).' line above a paged table."""
    return f"Showing {page['returned_count']} {what} ({order})."
