"""Thin async client for the platform API.

Every call carries the end user's own bearer token, so the API's access rules (company,
visibility tier) apply per user. This server holds no credentials of its own.
"""

from typing import Any

import httpx
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.exceptions import ToolError

from app.config import settings
from app.errors import describe_status, describe_transport_error


def bearer_header(ctx: Context) -> str:
    """The caller's Authorization header, from the incoming MCP HTTP request."""
    request = ctx.request_context.request
    header = request.headers.get("authorization") if request is not None else None
    if not header or not header.lower().startswith("bearer "):
        raise ToolError("Not authenticated: no bearer token was sent with this request.")
    return header


class ApiClient:
    def __init__(self, authorization: str):
        self._authorization = authorization

    @classmethod
    def for_request(cls, ctx: Context) -> "ApiClient":
        return cls(bearer_header(ctx))

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET path and return the JSON body. Failures raise ToolError with an LLM-readable message."""
        params = {key: value for key, value in (params or {}).items() if value is not None}
        try:
            async with httpx.AsyncClient(
                base_url=settings.api_base_url, timeout=settings.api_timeout_seconds
            ) as client:
                response = await client.get(
                    path, params=params, headers={"Authorization": self._authorization}
                )
        except httpx.HTTPError as error:
            raise ToolError(describe_transport_error(error)) from error
        if response.is_error:
            raise ToolError(describe_status(response))
        return response.json()
