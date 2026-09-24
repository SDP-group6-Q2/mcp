"""Where the manual PDFs come from: the Supabase bucket, or a local folder for development."""

import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

MANUAL_SUFFIX = "_manual_EN.pdf"


@dataclass(frozen=True)
class ManualFile:
    serial_number: str
    filename: str
    data: bytes


def serial_from_filename(filename: str) -> str | None:
    """'15610_manual_EN.pdf' -> '15610' (the serial number is the join key to the machine)."""
    return filename[: -len(MANUAL_SUFFIX)] if filename.endswith(MANUAL_SUFFIX) else None


def local_manuals(directory: Path, only_serial: str | None = None) -> Iterator[ManualFile]:
    for path in sorted(directory.glob(f"*{MANUAL_SUFFIX}")):
        serial = serial_from_filename(path.name)
        if serial and (only_serial is None or serial == only_serial):
            yield ManualFile(serial, path.name, path.read_bytes())


def _bucket_manuals(only_serial: str | None) -> list[ManualFile]:
    from supabase import create_client

    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (or use --from-dir).")
    bucket = create_client(settings.supabase_url, settings.supabase_service_role_key).storage.from_(
        settings.manuals_bucket
    )
    manuals = []
    for entry in bucket.list():
        serial = serial_from_filename(entry["name"])
        if serial and (only_serial is None or serial == only_serial):
            manuals.append(ManualFile(serial, entry["name"], bucket.download(entry["name"])))
    return manuals


async def bucket_manuals(only_serial: str | None = None) -> list[ManualFile]:
    return await asyncio.to_thread(_bucket_manuals, only_serial)
