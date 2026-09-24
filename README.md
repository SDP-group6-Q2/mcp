# mcp server

MCP server that exposes the AROL platform API to an AI agent as tools. Each tool calls an API
endpoint and returns the result formatted as text an LLM can use directly.

- **Transport:** streamable HTTP, endpoint `/mcp` on port 9000.
- **Auth:** the agent sends the end user's bearer token in the `Authorization` header of every MCP
  request. Tools forward it to the API, so the API's access rules (company, visibility tier) apply
  per user. This server holds no credentials of its own.
- **Errors:** API failures become tool errors with an LLM-readable message (`app/errors.py`).
  A denial is stated explicitly and is never turned into an empty result.

## Layout

```
app/
  main.py         builds the server and registers the domains
  config.py       settings (API_BASE_URL, MCP_HOST, MCP_PORT)
  api_client.py   async API client that forwards the caller's token
  errors.py       API status -> LLM-readable message
  formatting.py   shared markdown helpers
  domains/
    technical/    machines, telemetry, alarms, maintenance, manuals
    commercial/   quotes, orders, shipments
```

Each domain has `tools.py` (registers `@mcp.tool` functions that call the API) and `formatters.py`
(pure functions turning API JSON into text; unit-tested without a server).

## Adding a tool

1. Add a formatter to the domain's `formatters.py` and a test in `tests/`.
2. Add an `@mcp.tool()` in the domain's `tools.py`: call `ApiClient.for_request(ctx).get(...)` and
   return the formatted text. Give it a docstring: that is what the model reads.
3. For a new domain, create the package with `register(mcp)` and add it to `DOMAINS` in `app/main.py`.

## Run

```bash
docker compose up -d mcp-server        # from the project root; reachable as http://mcp-server:9000/mcp
pip install -r requirements-dev.txt && pytest    # unit tests
```
