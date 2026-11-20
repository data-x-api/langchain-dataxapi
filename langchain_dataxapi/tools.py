"""DataXAPI tools for LangChain.

``DataXAPIFind`` searches the catalog of DataXAPI endpoints for free; ``DataXAPICall`` calls any of
them by ID. The tools in ``endpoint_tools`` each call one endpoint with its own typed arguments.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, ClassVar

from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from langchain_core.utils import secret_from_env
from pydantic import BaseModel, Field, SecretStr, field_validator

from langchain_dataxapi._client import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DataXAPIClient,
    DataXAPIError,
    summarize,
)

_DOCS = "https://dataxapi.com"


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


class DataXAPIBaseTool(BaseTool):
    """Base of the DataXAPI tools: the API key, the HTTP client and the shape of an answer.

    Setup:
        .. code-block:: bash

            pip install -U langchain-dataxapi
            export DATAXAPI_API_KEY="dx_..."

    A tool answers with a JSON string: ``data`` (an ``items`` list or one ``item``), ``page``
    (``next_cursor`` for the next page), ``billing`` (``amount`` charged in US dollars and
    ``balance_after``) and ``request_id``. An error comes back as the tool's answer, naming the error
    code, whether anything was charged and whether to retry, so an agent can correct itself; set
    ``handle_tool_error=False`` to raise ``ToolException`` instead.
    """

    api_key: SecretStr | None = Field(default_factory=secret_from_env("DATAXAPI_API_KEY", default=None))
    """DataXAPI API key. Read from ``DATAXAPI_API_KEY`` when left out."""
    base_url: str = DEFAULT_BASE_URL
    """API base URL."""
    timeout: float = DEFAULT_TIMEOUT
    """Seconds to wait for one answer."""
    transport: Any = Field(default=None, exclude=True, repr=False)
    """An ``httpx`` transport to send requests through instead of the network (tests, proxies)."""
    handle_tool_error: bool | str | Callable[[ToolException], str] | None = True

    def _client(self) -> DataXAPIClient:
        return DataXAPIClient(
            self.api_key.get_secret_value() if self.api_key else None,
            base_url=self.base_url,
            timeout=self.timeout,
            transport=self.transport,
        )


class DataXAPIEndpointTool(DataXAPIBaseTool):
    """One DataXAPI endpoint with typed arguments. The generated tools set the class variables."""

    endpoint: ClassVar[str] = ""
    """The endpoint's ID, such as ``douyin.videos.comments.list``."""
    one_of: ClassVar[tuple[str, ...]] = ()
    """Arguments of which at least one must be given, such as ``("id", "url")``."""
    example: ClassVar[dict[str, Any]] = {}
    """Example arguments, from the endpoint's recorded example."""

    def _params(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        params = {k: v for k, v in kwargs.items() if v is not None and v != "" and v != []}
        if self.one_of and not any(name in params for name in self.one_of):
            raise ToolException(f"Give one of: {', '.join(self.one_of)}. Nothing was sent, so nothing was charged.")
        return params

    def _run(self, run_manager: CallbackManagerForToolRun | None = None, **kwargs: Any) -> str:
        params = self._params(kwargs)
        try:
            envelope = self._client().call(self.endpoint, params)
        except DataXAPIError as exc:
            raise ToolException(exc.describe()) from exc
        return _dump(summarize(envelope))

    async def _arun(self, run_manager: AsyncCallbackManagerForToolRun | None = None, **kwargs: Any) -> str:
        params = self._params(kwargs)
        try:
            envelope = await self._client().acall(self.endpoint, params)
        except DataXAPIError as exc:
            raise ToolException(exc.describe()) from exc
        return _dump(summarize(envelope))


class DataXAPIFindInput(BaseModel):
    """Arguments of dataxapi_find."""

    query: str = Field(
        description="The data needed, in plain words, Chinese or English, for example "
        "'xiaohongshu note comments', '公众号文章阅读数' or 'douyin keyword trend'."
    )
    platform: str | None = Field(
        default=None,
        description="Optional platform ID to narrow the search, such as douyin, xiaohongshu, wechat_mp, "
        "wechat_channels, wechat, weibo, bilibili, zhihu, kuaishou, tiktok, youtube, x, reddit.",
    )


class DataXAPIFind(DataXAPIBaseTool):
    """Find the DataXAPI endpoint for a need described in plain words. Free; needs no API key.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIFind

            tool = DataXAPIFind()
            tool.invoke({"query": "xiaohongshu note comments"})
    """

    name: str = "dataxapi_find"
    description: str = (
        "Free. Searches DataXAPI's catalog of social media and market data endpoints (Douyin, Xiaohongshu, "
        "WeChat Official Accounts, WeChat Channels, WeChat Search, Weibo, Bilibili, Zhihu, Kuaishou, TikTok, "
        "YouTube, X, Reddit and more) by a need described in plain words, Chinese or English. Returns endpoint "
        "IDs with what each returns, its price, required parameters and example parameters. Call the one that "
        "fits with dataxapi_call. Use it when no other DataXAPI tool fits the task."
    )
    args_schema: type[BaseModel] = DataXAPIFindInput

    @staticmethod
    def _answer(payload: dict[str, Any]) -> str:
        data = payload.get("data") or {}
        matches = []
        for m in data.get("matches") or []:
            if m.get("type") != "capability":
                continue
            pricing = m.get("pricing") or {}
            matches.append(
                {
                    "endpoint": m.get("id"),
                    "name": (m.get("name") or {}).get("en"),
                    "summary": (m.get("summary") or {}).get("en"),
                    "required": m.get("required") or [],
                    "one_of": m.get("one_of") or [],
                    "price_usd": pricing.get("price"),
                    "per": pricing.get("per"),
                    "example_params": (m.get("example") or {}).get("params"),
                    "docs": _DOCS + (m.get("url") or "/apis/"),
                }
            )
        out: dict[str, Any] = {"matches": matches}
        if data.get("unknown"):
            out["not_covered"] = data["unknown"]
        if matches:
            out["next"] = (
                "Call one with dataxapi_call: endpoint = matches[i].endpoint, params = an object like "
                "example_params. Each call is charged at that endpoint's price; errors are not charged."
            )
        else:
            out["next"] = "Nothing matched. Try other words, or browse https://dataxapi.com/apis/."
        return _dump(out)

    def _run(
        self, query: str, platform: str | None = None, run_manager: CallbackManagerForToolRun | None = None
    ) -> str:
        try:
            return self._answer(self._client().find(query, platform))
        except DataXAPIError as exc:
            raise ToolException(exc.describe()) from exc

    async def _arun(
        self, query: str, platform: str | None = None, run_manager: AsyncCallbackManagerForToolRun | None = None
    ) -> str:
        try:
            return self._answer(await self._client().afind(query, platform))
        except DataXAPIError as exc:
            raise ToolException(exc.describe()) from exc


class DataXAPICallInput(BaseModel):
    """Arguments of dataxapi_call."""

    endpoint: str = Field(
        description="The endpoint ID, dot-separated, such as douyin.users.get or xiaohongshu.notes.comments.list. "
        "Find it with dataxapi_find."
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description='The endpoint\'s parameters as an object, for example {"query": "coffee", "sort": "latest"}. '
        'Add "cursor" with the last answer\'s page.next_cursor for the next page.',
    )

    @field_validator("params", mode="before")
    @classmethod
    def _parse_json(cls, value: Any) -> Any:
        """Accept the parameters as a JSON string too."""
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return {}
            try:
                return json.loads(text)
            except ValueError:
                raise ValueError("params must be a JSON object") from None
        return value


class DataXAPICall(DataXAPIBaseTool):
    """Call any DataXAPI endpoint by its ID, with its parameters as JSON.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPICall

            tool = DataXAPICall()
            tool.invoke({"endpoint": "douyin.users.get", "params": {"id": "MS4wLjABAAAA..."}})
    """

    name: str = "dataxapi_call"
    description: str = (
        "Calls any DataXAPI endpoint by its ID (for example douyin.users.get, bilibili.videos.search, "
        "x.posts.search) with its parameters as a JSON object, and returns one page of data. Find the endpoint "
        "ID, its parameters and price with dataxapi_find (free) first. Each call is charged at that endpoint's "
        "price (shown by dataxapi_find); errors are not charged, and every answer says what it cost in "
        "billing.amount (US dollars). For the next page, call again with cursor set to page.next_cursor; each "
        "page is charged on its own. No sign-in to the user's own platform account is needed."
    )
    args_schema: type[BaseModel] = DataXAPICallInput

    def _run(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            return _dump(summarize(self._client().call(endpoint.strip(), params or {})))
        except DataXAPIError as exc:
            raise ToolException(exc.describe()) from exc

    async def _arun(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            return _dump(summarize(await self._client().acall(endpoint.strip(), params or {})))
        except DataXAPIError as exc:
            raise ToolException(exc.describe()) from exc
