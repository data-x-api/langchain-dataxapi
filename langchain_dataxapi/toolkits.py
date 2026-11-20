"""All DataXAPI tools as one toolkit."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, BaseToolkit
from langchain_core.utils import secret_from_env
from pydantic import Field, SecretStr

from langchain_dataxapi._client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from langchain_dataxapi.endpoint_tools import ENDPOINT_TOOLS
from langchain_dataxapi.tools import DataXAPIBaseTool, DataXAPICall, DataXAPIFind


class DataXAPIToolkit(BaseToolkit):
    """The DataXAPI tools: find an endpoint (free), call any endpoint, and one tool per popular endpoint.

    Setup:
        .. code-block:: bash

            pip install -U langchain-dataxapi
            export DATAXAPI_API_KEY="dx_..."

    Example:
        .. code-block:: python

            from langchain.agents import create_agent
            from langchain_dataxapi import DataXAPIToolkit

            agent = create_agent("claude-sonnet-4-6", DataXAPIToolkit().get_tools())
            question = "What are people saying about 露营 on Xiaohongshu?"
            agent.invoke({"messages": [{"role": "user", "content": question}]})
    """

    api_key: SecretStr | None = Field(default_factory=secret_from_env("DATAXAPI_API_KEY", default=None))
    """DataXAPI API key. Read from ``DATAXAPI_API_KEY`` when left out."""
    base_url: str = DEFAULT_BASE_URL
    """API base URL."""
    timeout: float = DEFAULT_TIMEOUT
    """Seconds to wait for one answer."""
    endpoint_tools: bool = True
    """Include the one-endpoint tools. False gives only ``dataxapi_find`` and ``dataxapi_call``."""
    transport: Any = Field(default=None, exclude=True, repr=False)
    """An ``httpx`` transport to send requests through instead of the network (tests, proxies)."""

    def get_tools(self) -> list[BaseTool]:
        """dataxapi_find and dataxapi_call first, then the one-endpoint tools by how much they are used."""
        classes: list[type[DataXAPIBaseTool]] = [DataXAPIFind, DataXAPICall]
        if self.endpoint_tools:
            classes.extend(ENDPOINT_TOOLS)
        return [
            cls(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout, transport=self.transport)  # type: ignore[call-arg]
            for cls in classes
        ]
