from typing import Literal

from mcp.server.fastmcp import Context, FastMCP

from app.api_client import ApiClient
from app.domains.technical import formatters


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_company_machines(ctx: Context) -> str:
        """List every machine owned by the current user's company, with model, serial number,
        plant location and PLC family."""
        machines = await ApiClient.for_request(ctx).get("/machines/")
        return formatters.machines_table(machines)

    @mcp.tool()
    async def get_machine_details(machine_id: str, ctx: Context) -> str:
        """Full details of one machine (e.g. MCH-0001) and its model: delivery date, plant location,
        as-built configuration profile, PLC family, software version, container/cap type."""
        machine = await ApiClient.for_request(ctx).get(f"/machines/{machine_id}")
        return formatters.machine_details(machine)

    @mcp.tool()
    async def get_latest_telemetry_snapshot(machine_id: str, ctx: Context) -> str:
        """The most recent hourly telemetry snapshot of a machine: operational status, production
        rate, uptime %, alarm count, temperature, energy use and health note."""
        snapshot = await ApiClient.for_request(ctx).get(f"/machines/{machine_id}/telemetry/latest")
        return formatters.telemetry_snapshot(snapshot)

    @mcp.tool()
    async def get_telemetry_summary(
        machine_id: str,
        ctx: Context,
        since: str | None = None,
        until: str | None = None,
        bucket: Literal["day", "week"] = "day",
    ) -> str:
        """Per-day or per-week telemetry aggregates for a machine (avg uptime %, avg production rate,
        alarm total, min/max temperature, avg energy). Use this for trend and pattern questions instead
        of get_telemetry_history: a month is ~30 rows here versus 720 raw hourly rows.
        Optional `since`/`until` restrict the period (ISO format, e.g. 2026-07-06 or 2026-07-06T14:00)."""
        rows = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/telemetry/summary",
            {"since": since, "until": until, "bucket": bucket},
        )
        return formatters.telemetry_summary(rows, bucket)

    @mcp.tool()
    async def get_telemetry_history(
        machine_id: str,
        ctx: Context,
        since: str | None = None,
        until: str | None = None,
        cursor: str | None = None,
    ) -> str:
        """Hourly telemetry snapshots of a machine, for inspecting a specific window of readings. For
        trends over more than a few days use get_telemetry_summary instead. Optional `since`/`until` restrict the period (ISO format, e.g. 2026-07-06 or 2026-07-06T14:00).
        Results are capped per call; when the output says more exist, call again with the `cursor` it gives."""
        page = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/telemetry", {"since": since, "until": until, "cursor": cursor}
        )
        return formatters.telemetry_history(page)

    @mcp.tool()
    async def get_alarm_summary(
        machine_id: str, ctx: Context, since: str | None = None, until: str | None = None
    ) -> str:
        """Alarm counts for a machine grouped by code and severity (occurrences, first/last seen, how many
        are still open). Use this for "why does this machine keep alarming" instead of listing every event
        with get_alarm_history. Optional `since`/`until` restrict the period (ISO format, e.g. 2026-07-06 or 2026-07-06T14:00)."""
        rows = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/alarms/summary", {"since": since, "until": until}
        )
        return formatters.alarm_summary(rows)

    @mcp.tool()
    async def get_alarm_history(
        machine_id: str,
        ctx: Context,
        since: str | None = None,
        until: str | None = None,
        cursor: str | None = None,
    ) -> str:
        """Individual alarm events of a machine, newest first, with code, severity and status. For
        recurring-alarm questions use get_alarm_summary first. Optional `since`/`until` restrict the period (ISO format, e.g. 2026-07-06 or 2026-07-06T14:00).
        Results are capped per call; when the output says more exist, call again with the `cursor` it gives."""
        page = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/alarms", {"since": since, "until": until, "cursor": cursor}
        )
        return formatters.alarm_history(page)

    @mcp.tool()
    async def get_maintenance_history(
        machine_id: str,
        ctx: Context,
        since: str | None = None,
        until: str | None = None,
        cursor: str | None = None,
    ) -> str:
        """A machine's maintenance tickets, newest first, each with the alarm that triggered it (blank when
        the ticket didn't originate from an alarm) - for correlating alarms with maintenance. `since`/`until`
        match the ticket's creation date (YYYY-MM-DD). Results are capped per call; when the output says more exist, call again with the `cursor` it gives."""
        page = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/maintenance", {"since": since, "until": until, "cursor": cursor}
        )
        return formatters.maintenance_history(page)

    @mcp.tool()
    async def get_company_maintenance_tickets(
        ctx: Context,
        since: str | None = None,
        until: str | None = None,
        cursor: str | None = None,
    ) -> str:
        """Maintenance tickets for all of the current user's company's machines, newest first.
        `since`/`until` match the ticket's creation date (YYYY-MM-DD). Results are capped per call; when the output says more exist, call again with the `cursor` it gives."""
        page = await ApiClient.for_request(ctx).get(
            "/maintenance-tickets/", {"since": since, "until": until, "cursor": cursor}
        )
        return formatters.company_tickets(page)
