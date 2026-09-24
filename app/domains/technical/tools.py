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
