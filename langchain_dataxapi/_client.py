"""A small DataXAPI HTTP client, sync and async, shared by every tool."""

from __future__ import annotations

import re
import uuid
from importlib import metadata
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.dataxapi.com"
DEFAULT_TIMEOUT = 90.0
SOURCE = "langchain"

try:
    _VERSION = metadata.version("langchain-dataxapi")
except metadata.PackageNotFoundError:  # running from a source checkout
    _VERSION = "0"
USER_AGENT = f"langchain-dataxapi/{_VERSION}"

# Endpoint IDs look like "douyin.videos.comments.list".
ENDPOINT_ID_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
# A request carrying one of these goes as POST with a JSON body.
BODY_PARAMS = frozenset({"ids", "keywords"})


class DataXAPIError(Exception):
    """An error answer from DataXAPI, or a failure to reach it."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int | None = None,
        request_id: str | None = None,
        charged: bool | None = False,
        retry: str | None = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status
        self.request_id = request_id
        self.charged = charged
        self.retry = retry

    def describe(self) -> str:
        """The error as one paragraph an agent can act on."""
        message = self.message if self.message.endswith((".", "。", "!", "?")) else self.message + "."
        parts = [f"DataXAPI error {self.code}: {message}"]
        if self.charged is False:
            parts.append("Nothing was charged.")
        elif self.charged is True:
            parts.append("This answer was charged as a call.")
        elif self.request_id:
            parts.append(f"Whether it was charged is not known; look the call up at /v1/calls/{self.request_id}.")
        if self.retry == "yes":
            parts.append("Retrying shortly may work.")
        elif self.retry == "after_fix":
            parts.append("Fix the request before trying again.")
        elif self.retry == "no":
            parts.append("Do not retry the same request.")
        elif self.retry:
            parts.append(f"Retry: {self.retry}.")
        if self.request_id:
            parts.append(f"Request ID: {self.request_id}.")
        return " ".join(parts)


def endpoint_path(endpoint_id: str) -> str:
    if not ENDPOINT_ID_RE.match(endpoint_id or ""):
        raise DataXAPIError(
            "invalid_endpoint",
            "The endpoint ID must look like 'douyin.videos.comments.list'; find one with dataxapi_find.",
        )
    return "/v1/" + endpoint_id.replace(".", "/")


def clean_params(params: dict[str, Any]) -> dict[str, Any]:
    """Drop empty values so optional arguments left out are not sent."""
    return {k: v for k, v in params.items() if v is not None and v != "" and v != []}


def to_query(params: dict[str, Any]) -> dict[str, str]:
    query: dict[str, str] = {}
    for key, value in params.items():
        if isinstance(value, bool):
            query[key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            query[key] = ",".join(str(v) for v in value)
        else:
            query[key] = str(value)
    return query


def summarize(envelope: dict[str, Any]) -> dict[str, Any]:
    """What an agent needs from an answer: the data, the next page, the charge and any warnings."""
    meta = envelope.get("meta") or {}
    out: dict[str, Any] = {
        "endpoint": meta.get("capability"),
        "data": envelope.get("data"),
        "page": envelope.get("page"),
        "billing": meta.get("billing"),
        "request_id": envelope.get("request_id"),
    }
    if envelope.get("warnings"):
        out["warnings"] = envelope["warnings"]
    return out


def _error(response: httpx.Response) -> DataXAPIError:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("code"), str):
        return DataXAPIError(
            payload["code"],
            str(payload.get("message") or "The request failed."),
            status=response.status_code,
            request_id=payload.get("request_id"),
            charged=payload.get("charged", False),
            retry=payload.get("retry"),
        )
    return DataXAPIError(
        "http_error",
        f"HTTP {response.status_code} without a DataXAPI answer.",
        status=response.status_code,
        charged=None,
    )


def _result(response: httpx.Response) -> dict[str, Any]:
    if response.is_success:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            return payload
    raise _error(response)


def _connection_error(exc: Exception) -> DataXAPIError:
    # The exception's name only: its text could carry the URL, never the key, but keep it short.
    return DataXAPIError("connection_error", f"Could not reach DataXAPI ({type(exc).__name__}).", charged=None)


class DataXAPIClient:
    """Calls DataXAPI. One page per call; each data call is charged on its own, errors are not."""

    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key or None
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    def _headers(self, *, needs_key: bool) -> dict[str, str]:
        if needs_key and not self._api_key:
            raise DataXAPIError(
                "unauthorized",
                "No DataXAPI API key. Set DATAXAPI_API_KEY or pass api_key; "
                "create one at https://dataxapi.com/console/keys/.",
                charged=False,
                retry="after_fix",
            )
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT, "X-Source": SOURCE}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if needs_key:
            # A fresh key per call: a call made again on purpose is a new call.
            headers["Idempotency-Key"] = str(uuid.uuid4())
        return headers

    @staticmethod
    def _plan(endpoint_id: str, params: dict[str, Any] | None) -> tuple[str, str, dict[str, Any]]:
        path = endpoint_path(endpoint_id)
        given = clean_params(params or {})
        if BODY_PARAMS.intersection(given):
            return "POST", path, {"json": given}
        return "GET", path, {"params": to_query(given)}

    def call(self, endpoint_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Fetch one page from one endpoint."""
        method, path, args = self._plan(endpoint_id, params)
        return self._send(method, path, needs_key=True, **args)

    async def acall(self, endpoint_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        method, path, args = self._plan(endpoint_id, params)
        return await self._asend(method, path, needs_key=True, **args)

    def find(self, query: str, platform: str | None = None) -> dict[str, Any]:
        """Endpoints for a need described in plain words, with price and parameters. Free, no key."""
        query_params = to_query(clean_params({"query": query, "platform": platform}))
        return self._send("GET", "/v1/catalog/search", needs_key=False, params=query_params)

    async def afind(self, query: str, platform: str | None = None) -> dict[str, Any]:
        query_params = to_query(clean_params({"query": query, "platform": platform}))
        return await self._asend("GET", "/v1/catalog/search", needs_key=False, params=query_params)

    def _send(self, method: str, path: str, *, needs_key: bool, **kwargs: Any) -> dict[str, Any]:
        headers = self._headers(needs_key=needs_key)
        try:
            with httpx.Client(transport=self._transport, timeout=self._timeout) as http:  # type: ignore[arg-type]
                response = http.request(method, self._base_url + path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise _connection_error(exc) from None
        return _result(response)

    async def _asend(self, method: str, path: str, *, needs_key: bool, **kwargs: Any) -> dict[str, Any]:
        headers = self._headers(needs_key=needs_key)
        try:
            async with httpx.AsyncClient(transport=self._transport, timeout=self._timeout) as http:  # type: ignore[arg-type]
                response = await http.request(method, self._base_url + path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise _connection_error(exc) from None
        return _result(response)
