from app.domains.technical import formatters as f
from app.formatting import num, short_ts

PAGE_NOTE = {"returned_count": 100, "truncated": True, "next_cursor": "abc"}


def test_short_ts_and_num():
    assert short_ts("2026-07-06T14:21:00") == "2026-07-06 14:21"
    assert short_ts("2026-08-01") == "2026-08-01"
    assert short_ts(None) is None
    assert num(91.60) == "91.6" and num(26104.3156, 0) == "26104" and num(None) is None and num(3.0) == "3"


def test_latest_snapshot_none_is_explicit():
    assert "No telemetry" in f.telemetry_snapshot(None)


def test_latest_snapshot_formats_values():
    text = f.telemetry_snapshot(
        {
            "machine_id": "MCH-0001",
            "timestamp": "2026-07-31T23:00:00",
            "operational_status": "Running",
            "production_rate_bph": 33338.4,
            "uptime_percentage": 91.6,
            "alarm_count": 0,
            "temperature_c": 45.6,
            "energy_kwh": 3.1,
            "health_note": None,
        }
    )
    assert "2026-07-31 23:00" in text and "33338" in text and "**Health note:** —" in text


def test_telemetry_summary_and_empty():
    row = {
        "bucket_start": "2026-07-06T00:00:00",
        "avg_uptime_percentage": 70.1869,
        "avg_production_rate_bph": 26104.3,
        "total_alarm_count": 15,
        "min_temperature_c": 20.3,
        "max_temperature_c": 50.5,
        "avg_energy_kwh": 2.418,
        "snapshot_count": 168,
    }
    text = f.telemetry_summary([row], "week")
    assert "Week starting" in text and "| 2026-07-06 | 70.2 | 26104 | 15 | 20.3–50.5 | 2.42 | 168 |" in text
    assert "No telemetry" in f.telemetry_summary([], "day")


def test_telemetry_history_page_note_only_when_truncated():
    row = {
        "timestamp": "2026-07-06T00:00:00",
        "operational_status": "Idle",
        "production_rate_bph": 0,
        "uptime_percentage": 0,
        "alarm_count": 0,
        "temperature_c": 21.0,
        "energy_kwh": 0.5,
        "health_note": "Idle",
    }
    done = f.telemetry_history({"rows": [row], "returned_count": 1, "truncated": False, "next_cursor": None})
    assert "cursor" not in done and "| 2026-07-06 00:00 | Idle | 0 | 0 | 0 | 21 | 0.5 | Idle |" in done
    more = f.telemetry_history({"rows": [row], **PAGE_NOTE})
    assert "cursor='abc'" in more
    assert "No telemetry snapshots" in f.telemetry_history({"rows": [], "returned_count": 0, "truncated": False})


def test_alarm_summary_and_history():
    summary = f.alarm_summary(
        [{"alarm_code": "AL082_MINIMUM_CAPS_LEVEL", "severity": "Low", "occurrence_count": 5,
          "first_seen": "2026-07-06T16:34:00", "last_seen": "2026-07-30T01:56:00", "open_count": 0}]
    )
    assert "| AL082_MINIMUM_CAPS_LEVEL | Low | 5 | 2026-07-06 16:34 | 2026-07-30 01:56 | 0 |" in summary
    assert "No alarms" in f.alarm_summary([])
    history = f.alarm_history(
        {"rows": [{"id": "ALM-0001", "timestamp": "2026-07-06T14:21:00", "alarm_code": "AL066", "severity": "High", "alarm_status": "Resolved"}],
         "returned_count": 1, "truncated": False, "next_cursor": None}
    )
    assert "| ALM-0001 | 2026-07-06 14:21 | AL066 | High | Resolved |" in history


def test_maintenance_history_keeps_tickets_without_alarm():
    page = {
        "rows": [
            {"id": "TCK-0060", "machine_id": "MCH-0001", "alarm_id": None, "ticket_type": "Size change assistance",
             "ticket_status": "Closed", "priority": "Low", "created_date": "2026-08-01", "owner_role": "Line Operator",
             "alarm_code": None, "severity": None, "alarm_status": None, "alarm_timestamp": None},
            {"id": "TCK-0001", "machine_id": "MCH-0001", "alarm_id": "ALM-0173", "ticket_type": "On-site service",
             "ticket_status": "Closed", "priority": "High", "created_date": "2026-07-07", "owner_role": "AROL Technical Service",
             "alarm_code": "AL010_X", "severity": "High", "alarm_status": "Resolved", "alarm_timestamp": "2026-07-06T10:00:00"},
        ],
        "returned_count": 2, "truncated": False, "next_cursor": None,
    }
    text = f.maintenance_history(page)
    assert "| TCK-0060 | 2026-08-01 | Size change assistance | Closed | Low | Line Operator | — | — | — |" in text
    assert "| ALM-0173 | AL010_X | High |" in text


def test_company_tickets_include_machine_column():
    page = {"rows": [{"id": "TCK-1", "machine_id": "MCH-0007", "alarm_id": None, "ticket_type": "Overhaul", "ticket_status": "Open",
                      "priority": "High", "created_date": "2026-07-07", "owner_role": None}],
            "returned_count": 1, "truncated": False, "next_cursor": None}
    assert "| TCK-1 | MCH-0007 | 2026-07-07 |" in f.company_tickets(page)
    assert "No maintenance tickets" in f.company_tickets({"rows": [], "returned_count": 0, "truncated": False})
