"""Paid calls against the live API: each costs that endpoint's price. Skipped unless DATAXAPI_API_KEY is set
and DATAXAPI_RUN_PAID=1."""

from __future__ import annotations

import json
import os

import pytest
from langchain_core.tools import BaseTool
from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_dataxapi import DataXAPITikTokVideoSearch, DataXAPIYouTubeTranscript

pytestmark = pytest.mark.skipif(
    not (os.environ.get("DATAXAPI_API_KEY") and os.environ.get("DATAXAPI_RUN_PAID") == "1"),
    reason="paid calls: set DATAXAPI_API_KEY and DATAXAPI_RUN_PAID=1",
)


class TestDataXAPITikTokVideoSearchIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[BaseTool]:
        return DataXAPITikTokVideoSearch

    @property
    def tool_constructor_params(self) -> dict:
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"query": "space station"}


def test_youtube_transcript() -> None:
    out = json.loads(DataXAPIYouTubeTranscript().invoke({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}))
    assert out["data"]
    assert out["billing"]["amount"] is not None
