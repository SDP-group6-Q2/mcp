"""What a client (the model) sees of every tool: descriptions, annotations, parameter docs."""

import asyncio

from app.main import mcp

TOOLS = asyncio.run(mcp.list_tools())


def test_all_twenty_one_tools_are_registered():
    assert len(TOOLS) == 21


def test_every_tool_is_declared_read_only_with_a_title():
    for tool in TOOLS:
        assert tool.annotations is not None and tool.annotations.readOnlyHint is True, tool.name
        assert tool.annotations.destructiveHint is False and tool.annotations.idempotentHint is True, tool.name
        assert tool.title, tool.name


def test_every_parameter_is_described_for_the_model():
    undocumented = [
        f"{tool.name}.{name}"
        for tool in TOOLS
        for name, schema in tool.inputSchema.get("properties", {}).items()
        if not schema.get("description")
    ]
    assert not undocumented, undocumented


def test_ctx_is_not_exposed_as_a_parameter():
    assert all("ctx" not in tool.inputSchema.get("properties", {}) for tool in TOOLS)


def test_ids_are_documented_with_examples():
    by_name = {tool.name: tool.inputSchema["properties"] for tool in TOOLS}
    assert "MCH-0001" in by_name["get_machine_details"]["machine_id"]["description"]
    assert "get_quote_revisions" in by_name["get_quote_lines"]["quote_revision_id"]["description"]


def test_every_tool_description_is_substantial():
    assert all(len(tool.description or "") > 60 for tool in TOOLS)


def test_ticket_and_alarm_lists_offer_status_and_priority_or_severity_filters():
    import json

    by_name = {tool.name: tool.inputSchema["properties"] for tool in TOOLS}
    for name in ("get_company_maintenance_tickets", "get_maintenance_history"):
        status, priority = json.dumps(by_name[name]["status"]), json.dumps(by_name[name]["priority"])
        assert '"open"' in status and "Waiting for parts" in status and "Waiting for parts" in by_name[name]["status"]["description"]
        assert '"Critical"' in priority
    alarms = by_name["get_alarm_history"]
    assert '"Acknowledged"' in json.dumps(alarms["status"]) and '"Critical"' in json.dumps(alarms["severity"])
