from mcp.server.fastmcp import Context, FastMCP

from app.api_client import ApiClient
from app.domains.commercial import formatters
from app.params import READ_ONLY, OrderId, QuoteId, QuoteRevisionId


def register(mcp: FastMCP) -> None:
    @mcp.tool(title="Quotes overview with status and totals", annotations=READ_ONLY)
    async def get_quotes_overview(ctx: Context) -> str:
        """Every quote of the company in one call, newest first: its status (the latest revision's), latest revision
        id, discount, line count, net total, validity date and the orders made from it, plus the net totals per
        status. Use it for any list, status overview, count, total or comparison across quotes (e.g. which quotes
        are open, their total value, which never became an order) instead of looking up quotes one by one."""
        quotes = await ApiClient.for_request(ctx).get("/quotes/overview")
        return formatters.quotes_overview(quotes)

    @mcp.tool(title="Orders overview with values and totals", annotations=READ_ONLY)
    async def get_orders_overview(ctx: Context) -> str:
        """Every order of the company in one call, newest first: quote, approved revision, order and shipment status,
        dates, line count and net value (from the quote's approved revision), plus the net totals per order year.
        Use it for any list, total, spend or year-on-year comparison across orders instead of looking up orders and
        quotes one by one."""
        orders = await ApiClient.for_request(ctx).get("/orders/overview")
        return formatters.orders_overview(orders)

    @mcp.tool(title="List the company's quotes", annotations=READ_ONLY)
    async def get_company_quotes(ctx: Context) -> str:
        """The company's quotes, newest first: id, currency, dates, description. A quote has no status of its own;
        the status is its latest revision's (get_latest_quote_revision)."""
        quotes = await ApiClient.for_request(ctx).get("/quotes/")
        return formatters.quotes_table(quotes)

    @mcp.tool(title="Quote details", annotations=READ_ONLY)
    async def get_quote_details(quote_id: QuoteId, ctx: Context) -> str:
        """Header of one quote: currency, creation and validity dates, description. Its currency applies
        to the quote's amounts."""
        quote = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}")
        return formatters.quote_details(quote)

    @mcp.tool(title="Quote revisions", annotations=READ_ONLY)
    async def get_quote_revisions(quote_id: QuoteId, ctx: Context) -> str:
        """Every revision of a quote, oldest first, with revision id, status, issue date, discount rate and what
        changed. The highest revision number is the current one. Use it to get a revision id for get_quote_lines or to
        see how a quote evolved."""
        revisions = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/revisions")
        return formatters.quote_revisions(revisions)

    @mcp.tool(title="Latest quote revision", annotations=READ_ONLY)
    async def get_latest_quote_revision(quote_id: QuoteId, ctx: Context) -> str:
        """Only the current (highest-numbered) revision of a quote: revision id, status, issue date, discount rate,
        what changed. The quickest way to a quote's current state and to the revision id of its latest lines."""
        revision = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/revisions/latest")
        return formatters.quote_revision(revision)

    @mcp.tool(title="Lines of a quote revision", annotations=READ_ONLY)
    async def get_quote_lines(quote_revision_id: QuoteRevisionId, ctx: Context) -> str:
        """The items of one quote revision: line id, machine (blank when not tied to a machine), net price and
        description. Prices are already net of the revision's discount and are shown with their currency.
        To compare two revisions, fetch both and compare."""
        lines = await ApiClient.for_request(ctx).get(f"/quotes/revisions/{quote_revision_id}/lines")
        return formatters.quote_lines(lines)

    @mcp.tool(title="Orders created from a quote", annotations=READ_ONLY)
    async def get_orders_by_quote(quote_id: QuoteId, ctx: Context) -> str:
        """The orders created from a quote, oldest first. An empty result means the quote never became an order."""
        orders = await ApiClient.for_request(ctx).get(f"/quotes/{quote_id}/orders")
        return formatters.orders_by_quote(orders)

    @mcp.tool(title="List the company's orders", annotations=READ_ONLY)
    async def get_company_orders(ctx: Context) -> str:
        """The company's orders, newest first, with quote id, order and shipment status, dates and currency."""
        orders = await ApiClient.for_request(ctx).get("/orders/")
        return formatters.orders_table(orders)

    @mcp.tool(title="Order details", annotations=READ_ONLY)
    async def get_order_details(order_id: OrderId, ctx: Context) -> str:
        """One order: originating quote id, order and shipment status, order date, expected delivery, currency and
        notes."""
        order = await ApiClient.for_request(ctx).get(f"/orders/{order_id}")
        return formatters.order_details(order)

    @mcp.tool(title="Fulfilment lines of an order", annotations=READ_ONLY)
    async def get_order_lines(order_id: OrderId, ctx: Context) -> str:
        """Fulfilment status of each line of an order. Order lines carry no item, quantity or price: what was ordered
        comes from the approved revision of the originating quote (get_order_details gives its quote id)."""
        lines = await ApiClient.for_request(ctx).get(f"/orders/{order_id}/lines")
        return formatters.order_lines(lines)
