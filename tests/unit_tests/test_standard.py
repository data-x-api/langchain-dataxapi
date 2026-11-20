"""LangChain's standard unit tests for tools (langchain-tests), one class per tool."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from langchain_tests.unit_tests import ToolsUnitTests

from langchain_dataxapi import ENDPOINT_TOOLS, DataXAPICall, DataXAPIFind

from .conftest import API_KEY


class _Standard(ToolsUnitTests):
    tool_class: type[BaseTool]
    invoke_example: dict[str, Any]

    @property
    def tool_constructor(self) -> type[BaseTool]:
        return self.tool_class

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": API_KEY}

    @property
    def tool_invoke_params_example(self) -> dict:
        return self.invoke_example

    @property
    def init_from_env_params(self) -> tuple[dict, dict, dict]:
        return {"DATAXAPI_API_KEY": "dx_env_key"}, {}, {"api_key": "dx_env_key"}


class TestDataXAPIFindStandard(_Standard):
    tool_class = DataXAPIFind
    invoke_example = {"query": "xiaohongshu note comments"}


class TestDataXAPICallStandard(_Standard):
    tool_class = DataXAPICall
    invoke_example = {"endpoint": "douyin.users.get", "params": {"id": "MS4wLjABAAAA"}}


# One standard test class per generated endpoint tool, named after it.
for _cls in ENDPOINT_TOOLS:
    _name = f"Test{_cls.__name__}Standard"
    globals()[_name] = type(_name, (_Standard,), {"tool_class": _cls, "invoke_example": dict(_cls.example)})
