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
