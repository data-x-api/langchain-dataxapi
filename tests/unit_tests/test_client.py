from __future__ import annotations

import httpx
import pytest

from langchain_dataxapi import DataXAPIClient, DataXAPIError

from .conftest import API_KEY, Recorder, error_body


def client(recorder: Recorder, key: str | None = API_KEY) -> DataXAPIClient:
    return DataXAPIClient(key, transport=recorder.transport)


def test_get_with_query_and_headers(recorder: Recorder) -> None:
    client(recorder).call("douyin.videos.search", {"query": "露营", "sort": None, "cursor": ""})
    req = recorder.last
    assert req.method == "GET"
    assert req.url.path == "/v1/douyin/videos/search"
    assert dict(req.url.params) == {"query": "露营"}
    assert req.headers["Authorization"] == f"Bearer {API_KEY}"
    assert req.headers["X-Source"] == "langchain"
    assert req.headers["User-Agent"].startswith("langchain-dataxapi/")
    assert req.headers["Idempotency-Key"]


def test_each_call_gets_a_new_idempotency_key(recorder: Recorder) -> None:
    c = client(recorder)
    c.call("douyin.videos.search", {"query": "a"})
    c.call("douyin.videos.search", {"query": "a"})
    assert recorder.requests[0].headers["Idempotency-Key"] != recorder.requests[1].headers["Idempotency-Key"]


def test_list_params_go_as_post_json(recorder: Recorder) -> None:
    client(recorder).call("douyin.index.keywords.history", {"keywords": ["咖啡", "CityWalk"], "since": "2026-09-01"})
    assert recorder.last.method == "POST"
    assert recorder.last_json() == {"keywords": ["咖啡", "CityWalk"], "since": "2026-09-01"}


def test_booleans_and_numbers_in_query(recorder: Recorder) -> None:
    client(recorder).call("x.posts.search", {"query": "a", "flag": True, "n": 3})
    assert dict(recorder.last.url.params) == {"query": "a", "flag": "true", "n": "3"}


def test_bad_endpoint_id_sends_nothing(recorder: Recorder) -> None:
    with pytest.raises(DataXAPIError) as err:
        client(recorder).call("../v1/account", {})
    assert err.value.code == "invalid_endpoint"
    assert recorder.requests == []


def test_no_key_sends_nothing(recorder: Recorder) -> None:
    with pytest.raises(DataXAPIError) as err:
        client(recorder, key=None).call("douyin.videos.search", {"query": "a"})
    assert err.value.code == "unauthorized"
    assert "Nothing was charged" in err.value.describe()
    assert recorder.requests == []


def test_find_needs_no_key(recorder: Recorder) -> None:
    recorder.body = {"code": "ok", "data": {"matches": []}}
    client(recorder, key=None).find("小红书评论", "xiaohongshu")
    req = recorder.last
    assert req.url.path == "/v1/catalog/search"
    assert dict(req.url.params) == {"query": "小红书评论", "platform": "xiaohongshu"}
    assert "Authorization" not in req.headers
    assert "Idempotency-Key" not in req.headers


@pytest.mark.parametrize(
    ("charged", "words"),
    [(False, "Nothing was charged."), (True, "was charged as a call"), ("unknown", "look the call up")],
)
def test_error_answer(recorder: Recorder, charged: object, words: str) -> None:
    recorder.status = 400
    recorder.body = error_body(charged=charged)
    with pytest.raises(DataXAPIError) as err:
        client(recorder).call("douyin.videos.search", {"query": "a"})
    assert err.value.code == "invalid_params"
    assert err.value.status == 400
    text = err.value.describe()
    assert words in text
    assert "Fix the request" in text
    assert "22222222-2222-4222-8222-222222222222" in text


def test_non_json_error(recorder: Recorder) -> None:
    recorder.status = 502
    recorder.body = "<html>bad gateway</html>"
    with pytest.raises(DataXAPIError) as err:
        client(recorder).call("douyin.videos.search", {"query": "a"})
    assert err.value.code == "http_error"
    assert err.value.charged is None


def test_connection_error_hides_key(recorder: Recorder) -> None:
    recorder.raise_error = httpx.ConnectError("boom")
    with pytest.raises(DataXAPIError) as err:
        client(recorder).call("douyin.videos.search", {"query": "a"})
    assert err.value.code == "connection_error"
    assert API_KEY not in err.value.describe()


async def test_async_call(recorder: Recorder) -> None:
    await client(recorder).acall("douyin.index.keywords.history", {"keywords": ["a"], "since": "x", "until": "y"})
    assert recorder.last.method == "POST"
    await client(recorder, key=None).afind("tiktok search")
    assert recorder.last.url.path == "/v1/catalog/search"
