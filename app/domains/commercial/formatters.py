from typing import Any

from app.formatting import bullets, table

_QUOTE_COLUMNS = [
    ("Quote", "id"),
    ("Currency", "currency"),
    ("Created", "created_at"),
    ("Valid until", "valid_until"),
    ("Description", "description"),
]


def quotes_table(quotes: list[dict[str, Any]]) -> str:
    if not quotes:
        return "The company has no quotes on record."
    return table(quotes, _QUOTE_COLUMNS)


def quote_revision(revision: dict[str, Any]) -> str:
    """Quotes have no status of their own: it lives on the revision, and the latest revision is current."""
    rate = revision["discount_rate"]
    return bullets(
        [
            ("Revision", revision["id"]),
            ("Quote", revision["quote_id"]),
            ("Revision number", revision["revision_number"]),
            ("Status", revision["revision_status"]),
            ("Issued", revision["issued_at"]),
            ("Discount rate", None if rate is None else f"{rate:.0%}"),
            ("Change summary", revision["change_summary"]),
        ]
    )
