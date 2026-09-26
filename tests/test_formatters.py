from app.domains.commercial import formatters as commercial
from app.domains.technical import formatters as technical
from app.formatting import page_note, table

MODEL = {
    "id": "MDL-100",
    "model_code": "TS-EURO-PK",
    "description": "Rotary closing machine",
    "primitive_diameter": None,
    "nominal_heads": 20,
    "container_type": "PET | glass",
    "cap_type": "Screw cap",
    "industry_segment": "Beverage",
    "notes": None,
}
MACHINE = {
    "id": "MCH-0001",
    "company_id": "CMP-001",
    "model_id": "MDL-100",
    "serial_number": "15610",
    "delivery_date": "2016-06-14",
    "plant_location": "Novara Plant 1",
    "configuration_profile": "Twin chute / 20 heads",
    "plc_family": "LINE-PLC-INTEGRATED",
    "software_version": "n/a",
    "model": MODEL,
}


def test_machines_table_lists_model_code():
    text = technical.machines_table([MACHINE])
    assert "| MCH-0001 | TS-EURO-PK | 15610 |" in text


def test_machines_table_empty_is_explicit():
    assert "no machines" in technical.machines_table([])


def test_machine_details_shows_missing_values_explicitly():
    text = technical.machine_details(MACHINE)
    assert "**Primitive diameter (mm):** —" in text
    assert "**Model notes:** —" in text


def test_table_cells_cannot_break_the_table():
    text = table([{"a": "x|y\nz"}], [("A", "a")])
    assert "x\\|y z" in text


def test_page_note_only_when_truncated():
    assert page_note({"truncated": False}) == ""
    note = page_note({"truncated": True, "returned_count": 100, "next_cursor": "abc"})
    assert "cursor='abc'" in note


def test_quote_revision_formats_discount():
    text = commercial.quote_revision(
        {
            "id": "QREV-0001",
            "quote_id": "QTE-1",
            "revision_number": 2,
            "revision_status": "Approved",
            "issued_at": "2025-03-10",
            "discount_rate": 0.05,
            "change_summary": None,
        }
    )
    assert "**Discount rate:** 5%" in text
    assert "**Change summary:** —" in text


def test_quotes_table_empty_is_explicit():
    assert "no quotes" in commercial.quotes_table([])


def test_zero_discount_is_shown_not_hidden():
    text = commercial.quote_revisions(
        [{"id": "QREV-1", "quote_id": "Q", "revision_number": 1, "revision_status": "Superseded",
          "issued_at": "2025-03-10", "discount_rate": 0, "change_summary": "Initial"}]
    )
    assert "| QREV-1 | 1 | Superseded | 2025-03-10 | 0% | Initial |" in text
    assert "highest revision number" in text
    assert "no revisions" in commercial.quote_revisions([])


def test_quote_lines_null_machine_currency_total_and_net_note():
    text = commercial.quote_lines(
        [{"id": "QLN-1", "quote_revision_id": "R", "machine_id": None, "price": 1200.5, "currency": "GBP", "description": "Kit"},
         {"id": "QLN-2", "quote_revision_id": "R", "machine_id": "MCH-0001", "price": None, "currency": "GBP", "description": "Service"}]
    )
    assert "| QLN-1 | — | 1200.5 GBP | Kit |" in text and "| QLN-2 | MCH-0001 | — | Service |" in text
    assert "Total (net): 1200.5 GBP" in text and "do not apply the discount again" in text
    assert "No lines were found" in commercial.quote_lines([])


def test_quote_lines_without_a_currency_still_render():
    text = commercial.quote_lines([{"id": "L", "quote_revision_id": "R", "machine_id": "M", "price": 10, "description": "x"}])
    assert "| L | M | 10 | x |" in text and "Total (net): 10." in text


ORDER = {"id": "ORD-1", "quote_id": "QTE-1", "company_id": "CMP-001", "order_status": "Closed", "order_date": "2025-04-08",
         "expected_delivery_date": "2025-06-24", "shipment_status": "Installed", "currency": "EUR", "notes": None}


def test_orders():
    assert "| ORD-1 | QTE-1 | Closed | Installed | 2025-04-08 | 2025-06-24 | EUR | — |" in commercial.orders_table([ORDER])
    assert "no orders" in commercial.orders_table([])
    assert "never became an order" in commercial.orders_by_quote([])
    assert "**Shipment:** Installed" in commercial.order_details(ORDER)
    lines = commercial.order_lines([{"id": "OLN-1", "order_id": "ORD-1", "fulfillment_status": "Delivered"}])
    assert "| OLN-1 | Delivered |" in lines and "fulfilment only" in lines
    assert "No fulfilment lines were found" in commercial.order_lines([])


def _overview_quote(id, status, total, currency="EUR", orders=()):
    return {"id": id, "currency": currency, "created_at": "2026-01-20", "valid_until": "2026-03-06", "description": "d",
            "latest_revision_id": f"REV-{id}", "latest_revision_number": 1, "status": status, "discount_rate": 0.06,
            "line_count": 2, "net_total": total, "order_ids": list(orders)}


def test_quotes_overview_lists_state_and_totals_per_status_without_mixing_currencies():
    text = commercial.quotes_overview([
        _overview_quote("Q1", "Draft", 10950.0),
        _overview_quote("Q2", "Approved", 15472.4, orders=["ORD-1", "ORD-2"]),
        _overview_quote("Q3", "Approved", 900.0, currency="GBP"),
        _overview_quote("Q4", "Draft", None),
    ])
    assert "| Q1 | Draft | REV-Q1 | 6% | 2 | 10950 EUR | 2026-03-06 | — | d |" in text
    assert "| Q2 | Approved | REV-Q2 | 6% | 2 | 15472.4 EUR | 2026-03-06 | ORD-1, ORD-2 | d |" in text
    assert "- Draft: 2 quote(s), 10950 EUR" in text
    assert "- Approved: 2 quote(s), 15472.4 EUR + 900 GBP" in text
    assert "- All: 4 quote(s), 26422.4 EUR + 900 GBP" in text
    assert "do not apply it again" in text
    assert "no quotes" in commercial.quotes_overview([])


def test_orders_overview_shows_value_and_totals_per_year():
    orders = [
        {**ORDER, "id": "ORD-3", "order_date": "2026-03-02", "quote_revision_id": "QREV-16", "line_count": 3, "net_total": 15472.4},
        {**ORDER, "id": "ORD-2", "order_date": "2025-08-05", "quote_revision_id": "QREV-9", "line_count": 4, "net_total": 15927.4},
        {**ORDER, "id": "ORD-1", "quote_revision_id": None, "line_count": 0, "net_total": None},
    ]
    text = commercial.orders_overview(orders)
    assert "| ORD-3 | QTE-1 | QREV-16 | Closed | Installed | 2026-03-02 | 2025-06-24 | 3 | 15472.4 EUR |" in text
    assert "| ORD-1 | QTE-1 | — | Closed | Installed | 2025-04-08 | 2025-06-24 | 0 | — |" in text
    assert "- 2026: 1 order(s), 15472.4 EUR" in text and "- 2025: 2 order(s), 15927.4 EUR" in text
    assert "- All: 3 order(s), 31399.8 EUR" in text
    assert "no orders" in commercial.orders_overview([])


def test_quote_details():
    text = commercial.quote_details({"id": "QTE-1", "company_id": "C", "currency": "EUR", "created_at": "2025-03-10",
                                     "valid_until": "2025-04-24", "description": None})
    assert "**Quote:** QTE-1" in text and "**Description:** —" in text
