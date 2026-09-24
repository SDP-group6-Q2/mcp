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
    async def get_quote_details(quote_id: str, ctx: Context) -> str:
        """Header of one quote (e.g. QTE-2025-0001): currency, creation and validity dates, description.
        Its status lives on the revisions: see get_quote_revisions."""
        quote = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}")
        return formatters.quote_details(quote)

    @mcp.tool()
    async def get_quote_revisions(quote_id: str, ctx: Context) -> str:
        """Every revision of a quote, oldest first, with status, issue date, discount rate and what
        changed. The highest revision number is the current one; earlier ones are superseded."""
        revisions = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/revisions")
        return formatters.quote_revisions(revisions)

    @mcp.tool()
    async def get_latest_quote_revision(quote_id: str, ctx: Context) -> str:
        """The current (highest-numbered) revision of a quote (e.g. QTE-2025-0001): its status,
        issue date, discount rate and what changed."""
        revision = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/revisions/latest")
        return formatters.quote_revision(revision)

    @mcp.tool()
    async def get_quote_lines(quote_revision_id: str, ctx: Context) -> str:
        """The items of one quote revision (e.g. QREV-0002) with machine and price. Quote lines belong to
        a revision, not to a quote: get the revision id from get_quote_revisions. Comparing two revisions
        means comparing their line sets. Prices are already net of the revision's discount."""
        lines = await ApiClient.for_request(ctx).get(f"/quotes/revisions/{quote_revision_id}/lines")
        return formatters.quote_lines(lines)

    @mcp.tool()
    async def get_orders_by_quote(quote_id: str, ctx: Context) -> str:
        """Orders created from a quote, oldest first. An empty result means the quote never became
        an order."""
        orders = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/orders")
        return formatters.orders_by_quote(orders)

    @mcp.tool()
    async def get_company_orders(ctx: Context) -> str:
        """The current user's company's orders, newest first, with order and shipment status."""
        orders = await ApiClient.for_request(ctx).get("/orders/")
        return formatters.orders_table(orders)

    @mcp.tool()
    async def get_order_details(order_id: str, ctx: Context) -> str:
        """One order (e.g. ORD-2025-0001): originating quote, order and shipment status, order date,
        expected delivery, currency and notes."""
        order = await ApiClient.for_request(ctx).get(f"/orders/{order_id}")
        return formatters.order_details(order)

    @mcp.tool()
    async def get_order_lines(order_id: str, ctx: Context) -> str:
        """Fulfilment status of each line of an order. Order lines carry no item, quantity or price: what
        was ordered comes from the quote lines of the approved revision of the originating quote."""
        lines = await ApiClient.for_request(ctx).get(f"/orders/{order_id}/lines")
        return formatters.order_lines(lines)
