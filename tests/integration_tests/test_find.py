"""Against the live API. dataxapi_find is free and needs no key, so these always run."""

from __future__ import annotations

import json

import pytest
from langchain_core.tools import BaseTool
from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_dataxapi import ENDPOINT_TOOLS, DataXAPIFind


class TestDataXAPIFindIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[BaseTool]:
        return DataXAPIFind

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"query": "xiaohongshu note comments"}


@pytest.mark.parametrize(
    ("query", "platform", "expected"),
    [
        ("小红书笔记评论", None, "xiaohongshu.notes.comments.list"),
        ("douyin keyword trend", None, "douyin.index.keywords.history"),
        ("YouTube transcript", "youtube", "youtube.videos.transcript.get"),
        ("公众号文章阅读数", "wechat_mp", "wechat_mp.articles.metrics"),
    ],
)
def test_find_live(query: str, platform: str | None, expected: str) -> None:
    out = json.loads(DataXAPIFind().invoke({"query": query, "platform": platform}))
    endpoints = [m["endpoint"] for m in out["matches"]]
    assert expected in endpoints
    match = out["matches"][endpoints.index(expected)]
    assert match["price_usd"]
    assert match["docs"].startswith("https://dataxapi.com/apis/")


async def test_find_live_async() -> None:
    out = json.loads(await DataXAPIFind().ainvoke({"query": "tiktok video search"}))
    assert "tiktok.videos.search" in [m["endpoint"] for m in out["matches"]]


@pytest.mark.parametrize("cls", ENDPOINT_TOOLS, ids=lambda c: c.endpoint)
def test_endpoint_tools_match_live_catalog(cls: type) -> None:
    """Each generated tool's endpoint is still in the live catalog."""
    out = json.loads(DataXAPIFind().invoke({"query": cls.endpoint}))
    assert cls.endpoint in [m["endpoint"] for m in out["matches"]]
