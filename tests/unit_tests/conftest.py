from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

API_KEY = "dx_test_not_a_real_key"


def ok_envelope(items: list[dict] | None = None, cursor: str | None = None, amount: str = "0.02") -> dict:
    return {
        "code": "ok",
        "request_id": "11111111-1111-4111-8111-111111111111",
        "data": {"items": items if items is not None else [{"id": "1", "text": "hello"}]},
        "page": {"next_cursor": cursor, "has_more": cursor is not None, "returned": 1},
        "warnings": [],
        "meta": {
            "capability": "test.endpoint",
            "fetched_at": "2026-11-20T00:00:00Z",
            "billing": {"amount": amount, "currency": "USD", "balance_after": "9.98"},
        },
    }


def error_body(code: str = "invalid_params", charged: Any = False, retry: str = "after_fix") -> dict:
    return {
        "code": code,
        "request_id": "22222222-2222-4222-8222-222222222222",
        "message": "A parameter is invalid",
        "charged": charged,
        "retry": retry,
    }


class Recorder:
    """An httpx transport that records each request and answers with a canned response."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.status = 200
        self.body: Any = ok_envelope()
        self.raise_error: Exception | None = None

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.raise_error is not None:
            raise self.raise_error
        if isinstance(self.body, (dict, list)):
            return httpx.Response(self.status, json=self.body)
        return httpx.Response(self.status, text=str(self.body))

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def last_json(self) -> Any:
        return json.loads(self.last.content)


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
def make_tool(recorder: Recorder) -> Callable[..., Any]:
    def make(cls: type, **kwargs: Any) -> Any:
        return cls(api_key=kwargs.pop("api_key", API_KEY), transport=recorder.transport, **kwargs)

    return make
