"""What a tool calls: excerpts from one manual, or an explicit reason there are none."""

import psycopg
from mcp.server.fastmcp.exceptions import ToolError

from app.rag import db
from app.rag.search import Excerpt, is_indexed, search_manual


class ManualNotIndexed(Exception):
    """The manual exists but hasn't been indexed for retrieval yet."""


async def manual_excerpts(serial_number: str, query: str) -> list[Excerpt]:
    """Top excerpts of the manual with this serial number. The caller has already authorized access."""
    try:
        conn = await db.connect()
    except psycopg.OperationalError as error:
        # The RAG database is only created by the first ingest.
        raise ManualNotIndexed() from error
    try:
        if not await is_indexed(conn, serial_number):
            raise ManualNotIndexed()
        return await search_manual(conn, serial_number, query)
    except psycopg.Error as error:
        raise ToolError("The manuals index is temporarily unavailable. Try again later.") from error
    finally:
        await conn.close()
