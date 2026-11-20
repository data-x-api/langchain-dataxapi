from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from langchain_core.messages import ToolMessage

from langchain_dataxapi import (
    ENDPOINT_TOOLS,
    DataXAPICall,
    DataXAPIDouyinKeywordTrend,
    DataXAPIDouyinVideoComments,
    DataXAPIFind,
    DataXAPIToolkit,
    DataXAPIXiaohongshuNoteSearch,
)

from .conftest import API_KEY, Recorder, error_body, ok_envelope

ALL_TOOLS = [DataXAPIFind, DataXAPICall, *ENDPOINT_TOOLS]


@pytest.mark.parametrize("cls", ENDPOINT_TOOLS, ids=lambda c: c.endpoint)
def test_endpoint_tool_sends_its_example(cls: type, make_tool: Callable, recorder: Recorder) -> None:
    out = json.loads(make_tool(cls).invoke(cls.example))
    req = recorder.last
    assert req.url.path == "/v1/" + cls.endpoint.replace(".", "/")
    sent = recorder.last_json() if req.method == "POST" else dict(req.url.params)
    assert set(sent) == set(cls.example)
    assert out["data"] == ok_envelope()["data"]
    assert out["billing"]["amount"] == "0.02"
    assert out["page"]["next_cursor"] is None


@pytest.mark.parametrize("cls", ENDPOINT_TOOLS, ids=lambda c: c.endpoint)
def test_endpoint_tool_states_price_and_errors(cls: type) -> None:
    text = cls.model_fields["description"].default
    assert "Price: $" in text
    assert "errors are not charged" in text
    assert cls.model_fields["name"].default == "dataxapi_" + cls.endpoint.replace(".", "_")
    cls.model_fields["args_schema"].default(**cls.example)


def test_tool_names_are_unique() -> None:
    names = [cls.model_fields["name"].default for cls in ALL_TOOLS]
    assert len(names) == len(set(names)) == 14


def test_optional_arguments_left_out_are_not_sent(make_tool: Callable, recorder: Recorder) -> None:
    make_tool(DataXAPIXiaohongshuNoteSearch).invoke({"query": "咖啡", "sort": "latest", "cursor": "c1"})
    assert dict(recorder.last.url.params) == {"query": "咖啡", "sort": "latest", "cursor": "c1"}


def test_enum_values_are_checked(make_tool: Callable, recorder: Recorder) -> None:
    with pytest.raises(ValueError):
        make_tool(DataXAPIXiaohongshuNoteSearch).invoke({"query": "咖啡", "sort": "oldest"})
    assert recorder.requests == []


def test_keyword_list_goes_as_post(make_tool: Callable, recorder: Recorder) -> None:
    args = {"keywords": ["咖啡", "奶茶"], "since": "2026-09-01", "until": "2026-09-30"}
    make_tool(DataXAPIDouyinKeywordTrend).invoke(args)
    assert recorder.last.method == "POST"
    assert recorder.last_json() == args


def test_one_of_missing_sends_nothing(make_tool: Callable, recorder: Recorder) -> None:
    out = make_tool(DataXAPIDouyinVideoComments).invoke({})
    assert "Give one of: id, url" in out
    assert "nothing was charged" in out
    assert recorder.requests == []


def test_error_comes_back_as_text(make_tool: Callable, recorder: Recorder) -> None:
    recorder.status = 404
    recorder.body = error_body(code="not_found", charged=False, retry="no")
    out = make_tool(DataXAPIDouyinVideoComments).invoke({"id": "1"})
    assert out.startswith("DataXAPI error not_found")
    assert "Nothing was charged." in out


def test_error_as_tool_message(make_tool: Callable, recorder: Recorder) -> None:
    recorder.status = 402
    recorder.body = error_body(code="insufficient_balance", retry="after_fix")
    msg = make_tool(DataXAPIDouyinVideoComments).invoke(
        {"type": "tool_call", "id": "call_1", "name": "dataxapi_douyin_videos_comments_list", "args": {"id": "1"}}
    )
    assert isinstance(msg, ToolMessage)
    assert msg.status == "error"
    assert "insufficient_balance" in msg.content


def test_raise_when_asked(make_tool: Callable, recorder: Recorder) -> None:
    from langchain_core.tools import ToolException

    recorder.status = 400
    recorder.body = error_body()
    with pytest.raises(ToolException):
        make_tool(DataXAPIDouyinVideoComments, handle_tool_error=False).invoke({"id": "1"})


def test_answer_keeps_chinese_readable(make_tool: Callable, recorder: Recorder) -> None:
    recorder.body = ok_envelope(items=[{"text": "好喝"}])
    out = make_tool(DataXAPIXiaohongshuNoteSearch).invoke({"query": "咖啡"})
    assert "好喝" in out


def test_warnings_pass_through(make_tool: Callable, recorder: Recorder) -> None:
    body = ok_envelope()
    body["warnings"] = [{"code": "partial", "message": "Some fields were not available."}]
    recorder.body = body
    out = json.loads(make_tool(DataXAPIXiaohongshuNoteSearch).invoke({"query": "咖啡"}))
    assert out["warnings"][0]["code"] == "partial"


async def test_async_endpoint_tool(make_tool: Callable, recorder: Recorder) -> None:
    out = json.loads(await make_tool(DataXAPIXiaohongshuNoteSearch).ainvoke({"query": "咖啡"}))
    assert out["billing"]["amount"] == "0.02"
    assert recorder.last.url.path == "/v1/xiaohongshu/notes/search"


async def test_async_one_of_missing(make_tool: Callable, recorder: Recorder) -> None:
    out = await make_tool(DataXAPIDouyinVideoComments).ainvoke({})
    assert "Give one of" in out
    assert recorder.requests == []


def test_find_shapes_matches(make_tool: Callable, recorder: Recorder) -> None:
    recorder.body = {
        "code": "ok",
        "data": {
            "matches": [
                {"type": "namespace", "id": "xiaohongshu"},
                {
                    "type": "capability",
                    "id": "xiaohongshu.notes.comments.list",
                    "url": "/apis/xiaohongshu/notes/comments/list/",
                    "name": {"zh": "小红书笔记评论", "en": "Xiaohongshu note comments"},
                    "summary": {"zh": "…", "en": "Get a page of comments."},
                    "required": [],
                    "one_of": ["id", "url"],
                    "pricing": {"per": "call", "price": "0.02"},
                    "example": {"params": {"id": "6a9c5884000000002b002d95"}},
                },
            ],
            "unknown": [],
        },
    }
    out = json.loads(make_tool(DataXAPIFind, api_key=None).invoke({"query": "小红书笔记评论"}))
    assert [m["endpoint"] for m in out["matches"]] == ["xiaohongshu.notes.comments.list"]
    match = out["matches"][0]
    assert match["price_usd"] == "0.02"
    assert match["one_of"] == ["id", "url"]
    assert match["docs"] == "https://dataxapi.com/apis/xiaohongshu/notes/comments/list/"
    assert "dataxapi_call" in out["next"]
    assert "not_covered" not in out


def test_find_with_nothing(make_tool: Callable, recorder: Recorder) -> None:
    recorder.body = {"code": "ok", "data": {"matches": [], "unknown": ["myspace"]}}
    out = json.loads(make_tool(DataXAPIFind).invoke({"query": "myspace friends"}))
    assert out["matches"] == []
    assert out["not_covered"] == ["myspace"]
    assert "Nothing matched" in out["next"]


async def test_async_find(make_tool: Callable, recorder: Recorder) -> None:
    recorder.body = {"code": "ok", "data": {"matches": []}}
    await make_tool(DataXAPIFind).ainvoke({"query": "a", "platform": "douyin"})
    assert dict(recorder.last.url.params) == {"query": "a", "platform": "douyin"}


@pytest.mark.parametrize("params", [{"id": "1", "cursor": "c"}, '{"id": "1", "cursor": "c"}'])
def test_call_takes_object_or_json(params: Any, make_tool: Callable, recorder: Recorder) -> None:
    make_tool(DataXAPICall).invoke({"endpoint": " douyin.users.get ", "params": params})
    assert recorder.last.url.path == "/v1/douyin/users/get"
    assert dict(recorder.last.url.params) == {"id": "1", "cursor": "c"}


def test_call_rejects_bad_json(make_tool: Callable, recorder: Recorder) -> None:
    with pytest.raises(ValueError):
        make_tool(DataXAPICall).invoke({"endpoint": "douyin.users.get", "params": "{id: 1"})
    assert recorder.requests == []


def test_call_rejects_bad_endpoint(make_tool: Callable, recorder: Recorder) -> None:
    out = make_tool(DataXAPICall).invoke({"endpoint": "douyin/users/get"})
    assert "invalid_endpoint" in out
    assert recorder.requests == []


async def test_async_call_tool(make_tool: Callable, recorder: Recorder) -> None:
    await make_tool(DataXAPICall).ainvoke({"endpoint": "douyin.index.keywords.history", "params": {"keywords": ["a"]}})
    assert recorder.last.method == "POST"


def test_toolkit(recorder: Recorder) -> None:
    tools = DataXAPIToolkit(api_key=API_KEY, transport=recorder.transport).get_tools()
    assert [t.name for t in tools[:2]] == ["dataxapi_find", "dataxapi_call"]
    assert len(tools) == 14
    assert all(t.api_key.get_secret_value() == API_KEY for t in tools)
    tools[2].invoke(type(tools[2]).example)
    assert recorder.last.headers["Authorization"] == f"Bearer {API_KEY}"


def test_toolkit_general_only() -> None:
    tools = DataXAPIToolkit(api_key=API_KEY, endpoint_tools=False).get_tools()
    assert [t.name for t in tools] == ["dataxapi_find", "dataxapi_call"]


def test_toolkit_reads_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATAXAPI_API_KEY", "dx_from_env")
    tools = DataXAPIToolkit().get_tools()
    assert tools[5].api_key.get_secret_value() == "dx_from_env"


def test_key_is_not_in_repr_or_schema() -> None:
    tool = DataXAPIXiaohongshuNoteSearch(api_key=API_KEY)
    assert API_KEY not in repr(tool)
    assert "api_key" not in json.dumps(tool.tool_call_schema.model_json_schema())
