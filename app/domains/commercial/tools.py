from mcp.server.fastmcp import Context, FastMCP

from app.api_client import ApiClient
from app.domains.commercial import formatters


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_company_quotes(ctx: Context) -> str:
        """List the current user's company's quotes, newest first. A quote has no status of its own:
        use get_latest_quote_revision for its current state."""
        quotes = await ApiClient.for_request(ctx).get("/quotes/")
        return formatters.quotes_table(quotes)

    @mcp.tool()
    async def get_latest_quote_revision(quote_id: str, ctx: Context) -> str:
        """The current (highest-numbered) revision of a quote (e.g. QTE-2025-0001): its status,
        issue date, discount rate and what changed."""
        revision = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/revisions/latest")
        return formatters.quote_revision(revision)
