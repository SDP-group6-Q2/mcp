"""MCP server exposing the platform API to an AI agent as tools.

    python -m app.main      # streamable HTTP on MCP_HOST:MCP_PORT, endpoint /mcp

Tools call the API with the caller's own bearer token (Authorization header of the MCP request)
and return LLM-readable text. Domains register themselves: add a domain by adding a package under
app/domains with a `register(mcp)` and listing it in DOMAINS.
"""

from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.domains import commercial, technical

DOMAINS = [technical, commercial]

_INSTRUCTIONS = (
    "Tools for AROL capping-machine customer support. Every call runs with the current user's "
    "permissions. If a tool reports access denied or not found, tell the user plainly; never "
    "guess, infer or answer from other data."
)


def create_server() -> FastMCP:
    mcp = FastMCP(
        "arol-mcp-server",
        instructions=_INSTRUCTIONS,
        host=settings.mcp_host,
        port=settings.mcp_port,
    )
    for domain in DOMAINS:
        domain.register(mcp)
    return mcp


mcp = create_server()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
