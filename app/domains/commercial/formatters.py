from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.formatting import bullets, cell, num, table

_QUOTE_COLUMNS = [
    ("Quote", "id"),
    ("Currency", "currency"),
    ("Created", "created_at"),
    ("Valid until", "valid_until"),
    ("Description", "description"),
]


def _amount(value: Any, currency: str | None) -> str | None:
    return None if value is None else f"{num(value, 2)} {currency or ''}".strip()


def _discount(rate: float | None) -> str | None:
    return None if rate is None else f"{rate:.0%}"


def _sum_by_currency(rows: list[dict[str, Any]]) -> str:
    """'26422.4 EUR + 900 GBP' over the rows' net_total, never mixing currencies ('—' when nothing is priced)."""
    totals: dict[str | None, float] = defaultdict(float)
    for row in rows:
        if row["net_total"] is not None:
            totals[row.get("currency")] += row["net_total"]
    return " + ".join(_amount(total, currency) for currency, total in totals.items()) or "—"


def _grouped_totals(rows: list[dict[str, Any]], group: Callable[[dict[str, Any]], Any], what: str) -> str:
    """One '- <group>: N <what>, <total>' line per group (in order of first appearance), then the overall line."""
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group(row)].append(row)
    lines = [f"- {cell(key)}: {len(members)} {what}, {_sum_by_currency(members)}" for key, members in groups.items()]
    lines.append(f"- All: {len(rows)} {what}, {_sum_by_currency(rows)}")
    return "\n".join(lines)


def quotes_overview(quotes: list[dict[str, Any]]) -> str:
    """Every quote with its current state and value, plus totals per status: listings and sums need no further
    calls."""
    if not quotes:
        return "The company has no quotes on record."
    shaped = [
        {
            **quote,
            "discount": _discount(quote["discount_rate"]),
            "net": _amount(quote["net_total"], quote["currency"]),
            "orders": ", ".join(quote["order_ids"]) or None,
        }
        for quote in quotes
    ]
    columns = [
        ("Quote", "id"),
        ("Status", "status"),
        ("Latest revision", "latest_revision_id"),
        ("Discount", "discount"),
        ("Lines", "line_count"),
        ("Total (net)", "net"),
        ("Valid until", "valid_until"),
        ("Orders", "orders"),
        ("Description", "description"),
    ]
    return (
        table(shaped, columns)
        + "\n\nTotals (net) by status of the latest revision:\n"
        + _grouped_totals(quotes, lambda q: q["status"], "quote(s)")
        + "\n\nA quote's status and total are its latest revision's; totals are already net of that revision's "
        "discount, so do not apply it again. Draft and Submitted quotes are still open; compare Valid until with "
        "today's date for validity. Orders — means the quote never became an order."
    )


def orders_overview(orders: list[dict[str, Any]]) -> str:
    """Every order with its value (the approved revision of its quote), plus totals per order year."""
    if not orders:
        return "The company has no orders on record."
    shaped = [{**order, "net": _amount(order["net_total"], order.get("currency"))} for order in orders]
    columns = [
        ("Order", "id"),
        ("Quote", "quote_id"),
        ("Approved revision", "quote_revision_id"),
        ("Status", "order_status"),
        ("Shipment", "shipment_status"),
        ("Ordered", "order_date"),
        ("Expected delivery", "expected_delivery_date"),
        ("Lines", "line_count"),
        ("Total (net)", "net"),
    ]
    return (
        table(shaped, columns)
        + "\n\nTotals (net) by order year:\n"
        + _grouped_totals(orders, lambda o: str(o["order_date"])[:4] if o["order_date"] else None, "order(s)")
        + "\n\nAn order's value is the net total of its quote's approved revision (already net of the discount). "
        "For the items themselves, call get_quote_lines with the approved revision id."
    )


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
    shaped = [{**line, "price_net": _amount(line["price"], line.get("currency"))} for line in lines]
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
        + f"\n\nTotal (net): {_amount(total, total_currency)}. Prices are already net of the revision's discount, in "
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
