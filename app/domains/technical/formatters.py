from typing import Any

from app.formatting import bullets, table

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
