"""Parameter types with descriptions, shared by the tools. The model reads these descriptions in the tool schema."""

from typing import Annotated, Literal

from mcp.types import ToolAnnotations
from pydantic import Field

# Every tool only reads data: clients can rely on that (e.g. to skip confirmation prompts).
READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True, destructiveHint=False, openWorldHint=False)

MachineId = Annotated[str, Field(description="Machine id, for example MCH-0001.")]

SinceDateTime = Annotated[
    str | None,
    Field(description="Only from this moment on. ISO date or datetime, e.g. 2026-07-06 or 2026-07-06T14:00. Omit for no lower limit."),
]
UntilDateTime = Annotated[
    str | None,
    Field(description="Only up to this moment. ISO date or datetime, e.g. 2026-07-31 or 2026-07-31T23:00. Omit for no upper limit."),
]
SinceDate = Annotated[
    str | None,
    Field(description="Only tickets created on or after this date, YYYY-MM-DD, e.g. 2026-07-01. Omit for no lower limit."),
]
UntilDate = Annotated[
    str | None,
    Field(description="Only tickets created on or before this date, YYYY-MM-DD, e.g. 2026-07-31. Omit for no upper limit."),
]
Cursor = Annotated[
    str | None,
    Field(description="Opaque token to get the next, older page: copy the cursor printed at the end of the previous page. Omit for the first page."),
]
# One value or a list of values: models often pass a single filter value as a plain string.
TicketStatus = Annotated[
    list[Literal["open", "Open", "In progress", "Waiting for parts", "Resolved", "Closed"]] | Literal["open", "Open", "In progress", "Waiting for parts", "Resolved", "Closed"] | None,
    Field(description="Only tickets with one of these statuses. 'open' means every ticket still needing work (Open, In progress or Waiting for parts): use it for 'open' or 'pending' tickets. Omit for all statuses."),
]
TicketPriority = Annotated[
    list[Literal["Critical", "High", "Medium", "Low"]] | Literal["Critical", "High", "Medium", "Low"] | None,
    Field(description="Only tickets with one of these priorities, e.g. ['Critical', 'High'] for urgent ones. Omit for all priorities."),
]
AlarmStatus = Annotated[
    list[Literal["Open", "Acknowledged", "Resolved"]] | Literal["Open", "Acknowledged", "Resolved"] | None,
    Field(description="Only alarms with one of these statuses, e.g. ['Open'] for alarms still active. Omit for all statuses."),
]
AlarmSeverity = Annotated[
    list[Literal["Critical", "High", "Medium", "Low"]] | Literal["Critical", "High", "Medium", "Low"] | None,
    Field(description="Only alarms with one of these severities, e.g. ['Critical']. Omit for all severities."),
]
Bucket = Annotated[Literal["day", "week"], Field(description="Aggregation period: 'day' for a fine trend, 'week' for a long one.")]

ManualQuery = Annotated[
    str,
    Field(description="What to look up, phrased in the manual's own technical terms with the key nouns, e.g. 'caps sorter door open' or 'closure head spindle pad clearance'. One topic; for an alarm use its description, not its code."),
]

QuoteId = Annotated[str, Field(description="Quote id, for example QTE-2025-0001.")]
QuoteRevisionId = Annotated[
    str,
    Field(description="Quote revision id, for example QREV-0002. Not a quote id: get it from get_quote_revisions or get_latest_quote_revision."),
]
OrderId = Annotated[str, Field(description="Order id, for example ORD-2025-0001.")]
