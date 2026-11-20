"""Writes the per-endpoint tools from DataXAPI's live catalog.

    uv run python scripts/generate_tools.py [catalog.json]

Reads https://api.dataxapi.com/v1/catalog (free, no key) unless a saved copy is given. For each endpoint in
CHOSEN it writes an argument schema and a tool class into langchain_dataxapi/endpoint_tools.py (descriptions,
parameters, allowed values and prices from the catalog), then the tool tables in README.md and
docs/dataxapi.mdx. Run it again when the catalog or the prices change; it overwrites what it wrote and
nothing else.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_URL = "https://api.dataxapi.com/v1/catalog"

# The endpoints the most DataXAPI accounts called in the 30 days to 2026-11-20 (internal accounts left out),
# in that order, then two for platforms abroad. Every other endpoint: DataXAPIFind and DataXAPICall.
CHOSEN = [
    ("xiaohongshu.notes.search", "DataXAPIXiaohongshuNoteSearch"),
    ("douyin.videos.search", "DataXAPIDouyinVideoSearch"),
    ("wechat_mp.accounts.articles.list", "DataXAPIWeChatOfficialAccountArticles"),
    ("douyin.videos.comments.list", "DataXAPIDouyinVideoComments"),
    ("douyin.videos.metrics", "DataXAPIDouyinVideoMetrics"),
    ("wechat_mp.articles.get", "DataXAPIWeChatArticle"),
    ("douyin.index.keywords.history", "DataXAPIDouyinKeywordTrend"),
    ("wechat.posts.search", "DataXAPIWeChatSearch"),
    ("wechat_channels.videos.search", "DataXAPIWeChatChannelsVideoSearch"),
    ("xiaohongshu.notes.comments.list", "DataXAPIXiaohongshuNoteComments"),
    ("tiktok.videos.search", "DataXAPITikTokVideoSearch"),
    ("youtube.videos.transcript.get", "DataXAPIYouTubeTranscript"),
]
SKIP_PARAMS = {"view", "fields", "include"}  # the tools always ask for the standard view
PY_TYPES = {
    "string": "str",
    "datetime": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string[]": "list[str]",
}
CURSOR_DOC = (
    "Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same "
    "other arguments; each page is charged on its own."
)
GLOSSED = re.compile(r"[\u4e00-\u9fff]+ \(([^)\u4e00-\u9fff]+)\)")
CJK = re.compile(r"\s*[（(][^)）]*[一-鿿][^)）]*[)）]|[一-鿿]+")


def english(text: str) -> str:
    """English text for English readers: a Chinese name glossed in brackets becomes the gloss, then
    Chinese names in brackets and any other Chinese are dropped."""
    text = GLOSSED.sub(r"\1", text)
    return re.sub(r"\s{2,}", " ", CJK.sub(" ", text)).strip()


def tool_name(endpoint: str) -> str:
    return "dataxapi_" + endpoint.replace(".", "_")


def input_name(cls: str) -> str:
    return cls + "Input"


def money(value: str) -> str:
    return "$" + format(Decimal(value).normalize(), "f")


def price_en(pricing: dict) -> str:
    if pricing["per"] == "item":
        return f"{money(pricing['price'])} per item, at most {money(pricing['max_charge'])} per call"
    return f"{money(pricing['price'])} per call"


def price_zh(pricing: dict) -> str:
    if pricing["per"] == "item":
        return f"每条 {money(pricing['price'])}，一次最多 {money(pricing['max_charge'])}"
    return f"{money(pricing['price'])} 一次"


def charge_en(pricing: dict) -> str:
    return "errors are not charged"


def charge_zh(pricing: dict) -> str:
    return "出错不收费"


def sentence(text: str) -> str:
    text = text.strip()
    return text if text.endswith((".", "!", "?")) else text + "."


def field_line(name: str, spec: dict, common: dict) -> tuple[str, bool]:
    """One pydantic field declaration, and whether it is required."""
    kind = (common.get(name) or {}).get("type", "string")
    values = spec.get("values")
    py = "Literal[" + ", ".join(repr(v) for v in values) + "]" if values else PY_TYPES.get(kind, "str")
    doc = (spec.get("doc") or {}).get("en") or (common.get(name) or {}).get("en") or name
    doc = sentence(english(doc))
    if spec.get("default"):
        doc += f" Default: {spec['default']}."
    example = spec.get("example")
    if example not in (None, "", []) and not values:
        doc += f" Example: {json.dumps(example, ensure_ascii=False)}."
    required = bool(spec.get("required"))
    if required:
        return f"    {name}: {py} = Field(description={doc!r})", True
    return f"    {name}: {py} | None = Field(default=None, description={doc!r})", False


def example_args(cap: dict) -> dict:
    """Required arguments plus the first of a one-of group, with the catalog's example values."""
    args = {}
    for name, spec in cap["params"].items():
        if spec.get("required") and spec.get("example") not in (None, ""):
            args[name] = spec["example"]
    one_of = cap.get("one_of") or []
    if one_of and not any(n in args for n in one_of):
        first = one_of[-1] if one_of[0] in ("keywords", "ids") else one_of[0]  # the single form reads easier
        args[first] = cap["params"][first]["example"]
    return args


def description(cap: dict) -> str:
    parts = [english(cap["summary"]["en"])]
    if cap.get("one_of"):
        parts.append(f"Give one of: {', '.join(cap['one_of'])}.")
    if "cursor" in cap.get("request_params", []):
        parts.append(
            "One call returns one page; for the next, call again with cursor set to page.next_cursor "
            "(charged on its own)."
        )
    pricing = cap["pricing"]
    parts.append(f"Price: {price_en(pricing)}; {charge_en(pricing)}.")
    parts.append("No sign-in to the user's own platform account is needed.")
    return " ".join(parts)


def tool_source(cap: dict, cls: str, common: dict) -> str:
    fields = [field_line(n, s, common) for n, s in cap["params"].items() if n not in SKIP_PARAMS]
    fields.sort(key=lambda f: not f[1])  # required first
    lines = [line for line, _ in fields]
    if "cursor" in cap.get("request_params", []):
        lines.append(f"    cursor: str | None = Field(default=None, description={CURSOR_DOC!r})")
    example = example_args(cap)
    pricing = cap["pricing"]
    example_code = json.dumps(example, ensure_ascii=False)
    return f'''

class {input_name(cls)}(BaseModel):
    """Arguments of {tool_name(cap["id"])}."""

{chr(10).join(lines)}


class {cls}(DataXAPIEndpointTool):
    """{english(cap["name"]["en"])} ({cap["id"]}).

    Price: {price_en(pricing)}; {charge_en(pricing)}.

    Example:
        .. code-block:: python

            from langchain_dataxapi import {cls}

            tool = {cls}()
            tool.invoke({example_code})
    """

    name: str = {tool_name(cap["id"])!r}
    description: str = {description(cap)!r}
    args_schema: type[BaseModel] = {input_name(cls)}
    endpoint: ClassVar[str] = {cap["id"]!r}
    one_of: ClassVar[tuple[str, ...]] = {tuple(cap.get("one_of") or ())!r}
    example: ClassVar[dict[str, Any]] = {example!r}
'''


def module_source(chosen: list[tuple[dict, str]], common: dict, revision: str, prices: str) -> str:
    head = f'''"""One LangChain tool per DataXAPI endpoint most used by DataXAPI's customers.

Written by scripts/generate_tools.py from catalog {revision}, price book {prices}. Do not edit by hand:
run the script again.
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field

from langchain_dataxapi.tools import DataXAPIEndpointTool
'''
    body = "".join(tool_source(cap, cls, common) for cap, cls in chosen)
    tail = "\n\nENDPOINT_TOOLS: tuple[type[DataXAPIEndpointTool], ...] = (\n"
    tail += "".join(f"    {cls},\n" for _, cls in chosen) + ")\n"
    return head + body + tail


def table(chosen: list[tuple[dict, str]], lang: str) -> str:
    if lang == "zh":
        rows = ["| 工具 | 类名 | 拿到什么 | 价格 |", "|---|---|---|---|"]
        rows.append("| `dataxapi_find` | `DataXAPIFind` | 用一句话描述要的数据，列出能用的接口、价格和参数 | 免费 |")
        rows.append("| `dataxapi_call` | `DataXAPICall` | 用接口编号加参数调用全部接口里的任何一个 | 按该接口的价格 |")
        for cap, cls in chosen:
            rows.append(
                f"| `{tool_name(cap['id'])}` | `{cls}` | {cap['name']['zh']} | "
                f"{price_zh(cap['pricing'])}，{charge_zh(cap['pricing'])} |"
            )
        return "\n".join(rows)
    rows = ["| Tool | Class | What it returns | Price |", "|---|---|---|---|"]
    rows.append(
        "| `dataxapi_find` | `DataXAPIFind` | Endpoints for a need described in plain words, "
        "with price and parameters | free |"
    )
    rows.append("| `dataxapi_call` | `DataXAPICall` | Any DataXAPI endpoint by its ID | that endpoint's price |")
    for cap, cls in chosen:
        summary = english(cap["summary"]["en"]).split(". ")[0].rstrip(".")
        rows.append(f"| `{tool_name(cap['id'])}` | `{cls}` | {summary} | {price_en(cap['pricing'])} |")
    return "\n".join(rows)


def replace_between(path: Path, start: str, end: str, text: str) -> None:
    body = path.read_text()
    if start not in body or end not in body:
        raise SystemExit(f"{path} has no {start} … {end} markers")
    before, rest = body.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(f"{before}{start}\n{text}\n{end}{after}")


def main() -> None:
    if len(sys.argv) > 1:
        catalog = json.loads(Path(sys.argv[1]).read_text())
    else:
        with urllib.request.urlopen(CATALOG_URL, timeout=60) as r:
            catalog = json.load(r)
    data = catalog["data"]
    caps = {c["id"]: c for c in data["capabilities"]}
    missing = [e for e, _ in CHOSEN if e not in caps]
    if missing:
        raise SystemExit(f"not in the catalog: {missing}")
    chosen = [(caps[e], cls) for e, cls in CHOSEN]
    target = ROOT / "langchain_dataxapi" / "endpoint_tools.py"
    target.write_text(module_source(chosen, data["params"], data["revision"], data["prices"]["version"]))
    subprocess.run(["ruff", "format", str(target)], check=False, capture_output=True)
    replace_between(ROOT / "README.md", "<!-- tools:start -->", "<!-- tools:end -->", table(chosen, "en"))
    replace_between(ROOT / "README.md", "<!-- tools-zh:start -->", "<!-- tools-zh:end -->", table(chosen, "zh"))
    replace_between(ROOT / "docs" / "dataxapi.mdx", "{/* tools:start */}", "{/* tools:end */}", table(chosen, "en"))
    print(f"{len(chosen)} endpoint tools from catalog {data['revision']}, price book {data['prices']['version']}")


if __name__ == "__main__":
    main()
