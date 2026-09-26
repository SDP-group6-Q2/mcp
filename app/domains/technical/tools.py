from mcp.server.fastmcp import Context, FastMCP

from app.api_client import ApiClient
from app.domains.technical import formatters
from app.params import (
    READ_ONLY,
    AlarmSeverity,
    AlarmStatus,
    Bucket,
    Cursor,
    MachineId,
    ManualQuery,
    SinceDate,
    SinceDateTime,
    TicketPriority,
    TicketStatus,
    UntilDate,
    UntilDateTime,
)
from app.rag.service import ManualNotIndexed, manual_excerpts


def register(mcp: FastMCP) -> None:
    @mcp.tool(title="List the company's machines", annotations=READ_ONLY)
    async def get_company_machines(ctx: Context) -> str:
        """Every machine owned by the current user's company: id, model, serial number, plant location and PLC
        family. Use it to see which machines exist or to find a machine id."""
        machines = await ApiClient.for_request(ctx).get("/machines/")
        return formatters.machines_table(machines)

    @mcp.tool(title="Machine details", annotations=READ_ONLY)
    async def get_machine_details(machine_id: MachineId, ctx: Context) -> str:
        """Full record of one machine and its model: delivery date, plant location, as-built configuration profile
        (nominal rate, heads, voltage, chuck), PLC family, software version, container and cap type. This is where
        a machine's own nominal production rate is found."""
        machine = await ApiClient.for_request(ctx).get(f"/machines/{machine_id}")
        return formatters.machine_details(machine)

    @mcp.tool(title="Latest telemetry reading", annotations=READ_ONLY)
    async def get_latest_telemetry_snapshot(machine_id: MachineId, ctx: Context) -> str:
        """The most recent hourly reading of a machine: operational status, production rate, uptime %, alarm count,
        temperature, energy use and health note. Use it for "how is the machine right now"."""
        snapshot = await ApiClient.for_request(ctx).get(f"/machines/{machine_id}/telemetry/latest")
        return formatters.telemetry_snapshot(snapshot)

    @mcp.tool(title="Telemetry trend (per day or week)", annotations=READ_ONLY)
    async def get_telemetry_summary(
        machine_id: MachineId,
        ctx: Context,
        since: SinceDateTime = None,
        until: UntilDateTime = None,
        bucket: Bucket = "day",
    ) -> str:
        """Per-day or per-week aggregates for a machine: average uptime %, average production rate, alarm total,
        min/max temperature, average energy. Prefer this for any trend, pattern or degradation question: a month is
        about 30 rows here against 720 hourly rows in get_telemetry_history."""
        rows = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/telemetry/summary",
            {"since": since, "until": until, "bucket": bucket},
        )
        return formatters.telemetry_summary(rows, bucket)

    @mcp.tool(title="Hourly telemetry readings", annotations=READ_ONLY)
    async def get_telemetry_history(
        machine_id: MachineId,
        ctx: Context,
        since: SinceDateTime = None,
        until: UntilDateTime = None,
        cursor: Cursor = None,
    ) -> str:
        """Raw hourly readings of a machine, for inspecting one specific window (narrow it with since/until). Not
        for trends over more than a few days: use get_telemetry_summary. Results are paged; the output says when more
        exist and gives the cursor for the next page."""
        page = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/telemetry", {"since": since, "until": until, "cursor": cursor}
        )
        return formatters.telemetry_history(page)

    @mcp.tool(title="Alarm summary by code", annotations=READ_ONLY)
    async def get_alarm_summary(
        machine_id: MachineId, ctx: Context, since: SinceDateTime = None, until: UntilDateTime = None
    ) -> str:
        """Alarms of a machine grouped by code and severity: occurrences, first and last seen, and how many are still
        open. Start here for "why does it keep alarming" and "any open alarms", before looking at individual events."""
        rows = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/alarms/summary", {"since": since, "until": until}
        )
        return formatters.alarm_summary(rows)

    @mcp.tool(title="Alarm events", annotations=READ_ONLY)
    async def get_alarm_history(
        machine_id: MachineId,
        ctx: Context,
        since: SinceDateTime = None,
        until: UntilDateTime = None,
        cursor: Cursor = None,
        status: AlarmStatus = None,
        severity: AlarmSeverity = None,
    ) -> str:
        """Individual alarm events of a machine, newest first, with code, severity and status. Use it to inspect
        specific recent events after get_alarm_summary; filter by status and severity to get exactly the alarms
        asked about (e.g. the open ones, or the critical ones since a date) instead of reading through all of them.
        Results are paged; the output gives the cursor for the next page."""
        page = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/alarms",
            {"since": since, "until": until, "cursor": cursor, "status": status, "severity": severity},
        )
        return formatters.alarm_history(page)

    @mcp.tool(title="Maintenance history of a machine", annotations=READ_ONLY)
    async def get_maintenance_history(
        machine_id: MachineId,
        ctx: Context,
        since: SinceDate = None,
        until: UntilDate = None,
        cursor: Cursor = None,
        status: TicketStatus = None,
        priority: TicketPriority = None,
    ) -> str:
        """One machine's maintenance tickets, newest first, each with the alarm that triggered it (blank when the
        ticket did not come from an alarm). Use it to correlate alarms with maintenance; filter by status and
        priority to get exactly the tickets asked about (e.g. status ['open'] for the open ones). Results are paged;
        the output gives the cursor for the next page."""
        page = await ApiClient.for_request(ctx).get(
            f"/machines/{machine_id}/maintenance",
            {"since": since, "until": until, "cursor": cursor, "status": status, "priority": priority},
        )
        return formatters.maintenance_history(page)

    @mcp.tool(title="Company maintenance tickets", annotations=READ_ONLY)
    async def get_company_maintenance_tickets(
        ctx: Context,
        since: SinceDate = None,
        until: UntilDate = None,
        cursor: Cursor = None,
        status: TicketStatus = None,
        priority: TicketPriority = None,
    ) -> str:
        """Maintenance tickets of all the company's machines, newest first, each with its machine. Use it for
        company-wide questions; no machine id needed. Filter by status and priority to get exactly the tickets asked
        about (e.g. status ['open'] for "what is open", plus priority ['Critical', 'High'] for urgent ones) instead
        of reading through all of them. Results are paged; the output gives the cursor for the next page."""
        page = await ApiClient.for_request(ctx).get(
            "/maintenance-tickets/",
            {"since": since, "until": until, "cursor": cursor, "status": status, "priority": priority},
        )
        return formatters.company_tickets(page)

    @mcp.tool(title="Search a machine's manual", annotations=READ_ONLY)
    async def get_manual_excerpts(machine_id: MachineId, query: ManualQuery, ctx: Context) -> str:
        """Search one machine's own use-and-maintenance manual and return the most relevant passages, each with its
        section and page. The source for how-to questions: operating and maintenance procedures, maintenance
        intervals, causes and remedies of faults, technical data, safety, ordering spare parts. If the passages
        don't answer the question, rephrase the query and search again."""
        if not query.strip():
            return "No query was provided. Ask a specific question about the manual."
        # The API checks the machine belongs to the user's company and returns its serial number, which
        # is what identifies the manual. Nothing is searched unless that check passes.
        machine = await ApiClient.for_request(ctx).get(f"/machines/{machine_id}")
        try:
            excerpts = await manual_excerpts(machine["serial_number"], query)
        except ManualNotIndexed:
            return formatters.manual_not_indexed(machine_id)
        return formatters.manual_excerpts(machine_id, excerpts)
