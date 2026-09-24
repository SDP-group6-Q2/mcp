"""API failures as messages an LLM can act on.

A denial must be stated explicitly, never returned as an empty result, and the model must not
guess or retry around it: these messages say so.
"""

import httpx

_MESSAGES = {
    400: "The request was invalid: {detail}",
    401: "Not authenticated: the session is missing or has expired.",
    403: "Access denied: the current user cannot access this information. Tell the user they "
    "don't have access; do not guess, infer or retry.",
    404: "Not found: {detail} Do not assume it was deleted or entered incorrectly.",
    422: "The request parameters were invalid: {detail}",
}
_UNAVAILABLE = "The data service is temporarily unavailable. Try again later."


def _detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):  # FastAPI validation errors: [{"loc": [...], "msg": "..."}]
        problems = []
        for item in detail:
            if isinstance(item, dict) and "msg" in item:
                field = ".".join(str(part) for part in item.get("loc", []) if part not in ("query", "path"))
                problems.append(f"{field}: {item['msg']}" if field else str(item["msg"]))
        return "; ".join(problems)
    return ""


def describe_status(response: httpx.Response) -> str:
    """LLM-readable message for a non-2xx API response."""
    template = _MESSAGES.get(response.status_code)
    if template is None:
        return _UNAVAILABLE
    return template.format(detail=_detail(response)).strip()


def describe_transport_error(error: httpx.HTTPError) -> str:
    if isinstance(error, httpx.TimeoutException):
        return "The data service took too long to answer. Try again later."
    return _UNAVAILABLE
