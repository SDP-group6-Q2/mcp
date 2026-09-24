import httpx

from app.errors import describe_status, describe_transport_error


def _response(status: int, body: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=body or {}, request=httpx.Request("GET", "http://api/x"))


def test_403_says_access_denied_and_forbids_guessing():
    message = describe_status(_response(403, {"detail": "You cannot access operational data."}))
    assert "Access denied" in message and "do not guess" in message


def test_404_includes_api_detail():
    assert "Quote 'X' not found." in describe_status(_response(404, {"detail": "Quote 'X' not found."}))


def test_unexpected_status_reads_as_unavailable():
    assert "temporarily unavailable" in describe_status(_response(500))


def test_timeout_is_distinguished():
    assert "too long" in describe_transport_error(httpx.ReadTimeout("t"))
    assert "unavailable" in describe_transport_error(httpx.ConnectError("c"))


def test_422_lists_the_offending_parameter():
    body = {"detail": [{"loc": ["query", "since"], "msg": "Input should be a valid datetime", "type": "x"}]}
    message = describe_status(_response(422, body))
    assert "since: Input should be a valid datetime" in message
