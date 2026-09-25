from typing import Any

from app.formatting import bullets, num, table

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


def quote_details(quote: dict[str, Any]) -> str:
    return bullets(
        [
            ("Quote", quote["id"]),
            ("Currency", quote["currency"]),
            ("Created", quote["created_at"]),
            ("Valid until", quote["valid_until"]),
            ("Description", quote["description"]),
        ]
    )


def quote_revisions(revisions: list[dict[str, Any]]) -> str:
    if not revisions:
        return "This quote has no revisions on record."
    shaped = [
        {**r, "discount": None if r["discount_rate"] is None else f"{r['discount_rate']:.0%}"}
        for r in revisions
    ]
    columns = [
        ("Revision", "id"),
        ("No.", "revision_number"),
        ("Status", "revision_status"),
        ("Issued", "issued_at"),
        ("Discount", "discount"),
        ("Change summary", "change_summary"),
    ]
    return table(shaped, columns) + "\n\nThe highest revision number is the current one."


def quote_lines(lines: list[dict[str, Any]]) -> str:
    if not lines:
        return (
            "No lines were found for this revision id: it either has no lines or does not exist "
            "(or belongs to another company). Check the id with get_quote_revisions."
        )
    def amount(value: Any, currency: str | None) -> str | None:
        return None if value is None else f"{num(value, 2)} {currency or ''}".strip()

    shaped = [{**line, "price_net": amount(line["price"], line.get("currency"))} for line in lines]
    total = sum(line["price"] for line in lines if line["price"] is not None)
    currencies = {line.get("currency") for line in lines if line["price"] is not None}
    total_currency = currencies.pop() if len(currencies) == 1 else None
    columns = [
        ("Line", "id"),
        ("Machine", "machine_id"),
        ("Price (net)", "price_net"),
        ("Description", "description"),
    ]
    return (
        table(shaped, columns)
        + f"\n\nTotal (net): {amount(total, total_currency)}. Prices are already net of the revision's discount, in "
        "the currency shown; do not apply the discount again. A machine of — means the line isn't tied to an "
        "installed machine."
    )


_ORDER_COLUMNS = [
    ("Order", "id"),
    ("Quote", "quote_id"),
    ("Status", "order_status"),
    ("Shipment", "shipment_status"),
    ("Ordered", "order_date"),
    ("Expected delivery", "expected_delivery_date"),
    ("Currency", "currency"),
    ("Notes", "notes"),
]


def orders_table(orders: list[dict[str, Any]]) -> str:
    if not orders:
        return "The company has no orders on record."
    return table(orders, _ORDER_COLUMNS)


def orders_by_quote(orders: list[dict[str, Any]]) -> str:
    if not orders:
        return "No order was created from this quote: it never became an order."
    return table(orders, _ORDER_COLUMNS)


def order_details(order: dict[str, Any]) -> str:
    return bullets([(label, order[key]) for label, key in _ORDER_COLUMNS])


def order_lines(lines: list[dict[str, Any]]) -> str:
    if not lines:
        return (
            "No fulfilment lines were found for this order id: it either has none or does not exist "
            "(or belongs to another company). Check the id with get_company_orders."
        )
    columns = [("Line", "id"), ("Fulfilment status", "fulfillment_status")]
    return (
        table(lines, columns)
        + "\n\nOrder lines track fulfilment only. What was ordered comes from the quote lines of "
        "the approved revision of the originating quote."
    )
