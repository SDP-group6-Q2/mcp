from typing import Any

from app.formatting import bullets, num, page_header, page_note, short_ts, table

_MACHINE_COLUMNS = [
    ("Machine", "id"),
    ("Model", "model_code"),
    ("Serial", "serial_number"),
    ("Plant", "plant_location"),
    ("PLC", "plc_family"),
]


def machines_table(machines: list[dict[str, Any]]) -> str:
    if not machines:
        return "The company has no machines on record."
    rows = [{**machine, "model_code": machine["model"]["model_code"]} for machine in machines]
    return table(rows, _MACHINE_COLUMNS)


def machine_details(machine: dict[str, Any]) -> str:
    model = machine["model"]
    return bullets(
        [
            ("Machine", machine["id"]),
            ("Serial number", machine["serial_number"]),
            ("Delivered", machine["delivery_date"]),
            ("Plant location", machine["plant_location"]),
            ("Configuration profile", machine["configuration_profile"]),
            ("PLC family", machine["plc_family"]),
            ("Software version", machine["software_version"]),
            ("Model", f"{model['model_code']} ({model['id']})"),
            ("Model description", model["description"]),
            ("Container type", model["container_type"]),
            ("Cap type", model["cap_type"]),
            ("Nominal heads", model["nominal_heads"]),
            ("Primitive diameter (mm)", model["primitive_diameter"]),
            ("Model notes", model["notes"]),
        ]
    )


def _rows(rows: list[dict[str, Any]], **derived: Any) -> list[dict[str, Any]]:
    """Copy rows adding derived cells: each kwarg is a function of the row."""
    return [{**row, **{key: fn(row) for key, fn in derived.items()}} for row in rows]


def telemetry_snapshot(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "No telemetry has been recorded for this machine."
    return bullets(
        [
            ("Machine", snapshot["machine_id"]),
            ("Time", short_ts(snapshot["timestamp"])),
            ("Operational status", snapshot["operational_status"]),
            ("Production rate (bph)", num(snapshot["production_rate_bph"], 0)),
            ("Uptime (%)", num(snapshot["uptime_percentage"])),
            ("Alarms in the hour", snapshot["alarm_count"]),
            ("Temperature (°C)", num(snapshot["temperature_c"])),
            ("Energy (kWh)", num(snapshot["energy_kwh"])),
            ("Health note", snapshot["health_note"]),
        ]
    )


def telemetry_summary(rows: list[dict[str, Any]], bucket: str) -> str:
    if not rows:
        return "No telemetry was recorded for that machine in that period."
    shaped = _rows(
        rows,
        start=lambda r: short_ts(r["bucket_start"])[:10],
        uptime=lambda r: num(r["avg_uptime_percentage"]),
        rate=lambda r: num(r["avg_production_rate_bph"], 0),
        temp=lambda r: f"{num(r['min_temperature_c'])}–{num(r['max_temperature_c'])}",
        energy=lambda r: num(r["avg_energy_kwh"], 2),
    )
    columns = [
        (f"{bucket.capitalize()} starting", "start"),
        ("Avg uptime %", "uptime"),
        ("Avg rate bph", "rate"),
        ("Alarms", "total_alarm_count"),
        ("Temp °C (min–max)", "temp"),
        ("Avg kWh", "energy"),
        ("Snapshots", "snapshot_count"),
    ]
    return table(shaped, columns)


def telemetry_history(page: dict[str, Any]) -> str:
    if not page["rows"]:
        return "No telemetry snapshots were found for that machine in that period."
    shaped = _rows(
        page["rows"],
        time=lambda r: short_ts(r["timestamp"]),
        rate=lambda r: num(r["production_rate_bph"], 0),
        uptime=lambda r: num(r["uptime_percentage"]),
        temp=lambda r: num(r["temperature_c"]),
        energy=lambda r: num(r["energy_kwh"], 2),
    )
    columns = [
        ("Time", "time"),
        ("Status", "operational_status"),
        ("Rate bph", "rate"),
        ("Uptime %", "uptime"),
        ("Alarms", "alarm_count"),
        ("Temp °C", "temp"),
        ("kWh", "energy"),
        ("Health note", "health_note"),
    ]
    return (
        page_header(page, "hourly snapshots", "oldest to newest within this page")
        + "\n\n"
        + table(shaped, columns)
        + page_note(page)
    )


def alarm_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No alarms were raised by that machine in that period."
    shaped = _rows(
        rows, first=lambda r: short_ts(r["first_seen"]), last=lambda r: short_ts(r["last_seen"])
    )
    columns = [
        ("Alarm code", "alarm_code"),
        ("Severity", "severity"),
        ("Occurrences", "occurrence_count"),
        ("First seen", "first"),
        ("Last seen", "last"),
        ("Still open", "open_count"),
    ]
    return table(shaped, columns)


def alarm_history(page: dict[str, Any]) -> str:
    if not page["rows"]:
        return "No alarms were found for that machine in that period."
    shaped = _rows(page["rows"], time=lambda r: short_ts(r["timestamp"]))
    columns = [
        ("Alarm", "id"),
        ("Time", "time"),
        ("Code", "alarm_code"),
        ("Severity", "severity"),
        ("Status", "alarm_status"),
    ]
    return page_header(page, "alarms", "newest first") + "\n\n" + table(shaped, columns) + page_note(page)


_TICKET_COLUMNS = [
    ("Ticket", "id"),
    ("Created", "created_date"),
    ("Type", "ticket_type"),
    ("Status", "ticket_status"),
    ("Priority", "priority"),
    ("Owner", "owner_role"),
    ("Alarm", "alarm_id"),
]


def maintenance_history(page: dict[str, Any]) -> str:
    """A machine's tickets with the alarm that triggered each (blank for tickets with no alarm)."""
    if not page["rows"]:
        return "No maintenance tickets were found for that machine in that period."
    columns = [*_TICKET_COLUMNS, ("Alarm code", "alarm_code"), ("Alarm severity", "severity")]
    return (
        page_header(page, "tickets", "newest first")
        + "\n\n"
        + table(page["rows"], columns)
        + page_note(page)
    )


def company_tickets(page: dict[str, Any]) -> str:
    if not page["rows"]:
        return "No maintenance tickets were found for the company's machines in that period."
    columns = [_TICKET_COLUMNS[0], ("Machine", "machine_id"), *_TICKET_COLUMNS[1:]]
    return (
        page_header(page, "tickets", "newest first")
        + "\n\n"
        + table(page["rows"], columns)
        + page_note(page)
    )
