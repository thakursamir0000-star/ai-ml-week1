"""Test doubles for the Anthropic API.

The fake sits at the HTTP layer (``httpx2.MockTransport``): the real
``anthropic`` SDK builds the request, parses the response and raises its own
typed exceptions, while nothing ever leaves the machine. Only the remote
server is faked; our parsing and validation code runs for real.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import anthropic
import httpx2

from src.api_client import ClaudeSettings, create_client

FAKE_API_KEY = "sk-ant-test-0000-not-a-real-key"


def text_block(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def thinking_block() -> dict[str, Any]:
    # claude-opus-5-5 always thinks; by default the thinking text comes back empty.
    return {"type": "thinking", "thinking": "", "signature": "test-signature"}


def message_body(*blocks: dict[str, Any], stop_reason: str = "end_turn", **extra: Any) -> dict[str, Any]:
    """A Messages API success body shaped like the real one."""
    body: dict[str, Any] = {
        "id": "msg_test_0001",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5-5",
        "content": list(blocks),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 42, "output_tokens": 17},
    }
    body.update(extra)
    return body


def error_body(error_type: str, message: str) -> dict[str, Any]:
    """A Messages API error body shaped like the real one."""
    return {"type": "error", "error": {"type": error_type, "message": message}, "request_id": "req_test_0001"}


def respond(status: int, body: dict[str, Any], headers: dict[str, str] | None = None) -> Callable[[httpx2.Request], httpx2.Response]:
    """Handler that always answers with the same status and JSON body."""
    return lambda request: httpx2.Response(status, json=body, headers=headers)


class FakeAnthropicAPI:
    """Stands in for api.anthropic.com and records every request it receives."""

    def __init__(self, handler: Callable[[httpx2.Request], httpx2.Response]) -> None:
        self._handler = handler
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return self._handler(request)

    @property
    def last_request(self) -> httpx2.Request:
        assert self.requests, "no request was sent"
        return self.requests[-1]

    @property
    def last_json(self) -> dict[str, Any]:
        return json.loads(self.last_request.content)

    def client(self, settings: ClaudeSettings) -> anthropic.Anthropic:
        # max_retries=0: SDK retries would only repeat the same canned answer.
        transport = httpx2.MockTransport(self)
        return create_client(settings, max_retries=0, http_client=httpx2.Client(transport=transport))
