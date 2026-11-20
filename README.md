# langchain-dataxapi

LangChain tools for [DataXAPI](https://dataxapi.com/?ref=langchain): public data from Douyin, Xiaohongshu (RedNote), WeChat Official Accounts, WeChat Channels, WeChat Search, Weibo, Bilibili, Zhihu and Kuaishou, plus Douyin's trend index, TikTok, YouTube, X and Reddit, for LangChain and LangGraph agents.

- **One key, 237 endpoints.** Twelve ready tools for the endpoints DataXAPI's customers call most, plus `dataxapi_find` (free) and `dataxapi_call`, which reach every endpoint.
- **No sign-in to your own platform account**, no cookies, no QR login.
- **Pay per call; errors are not charged.** Each tool's description states its price, and every answer says what that call cost (`billing.amount`, US dollars).
- **Free trial: up to 333 calls, no card.** Top up from $10; the balance does not expire.

中文说明见[下文](#中文说明)。

## Installation

```bash
pip install -U langchain-dataxapi
```

## Credentials

Create a key at <https://dataxapi.com/console/keys/?ref=langchain> (it starts with `dx_`) and set it:

```bash
export DATAXAPI_API_KEY="dx_..."
```

Or pass it to a tool or the toolkit: `DataXAPIToolkit(api_key="dx_...")`. `dataxapi_find` needs no key.

## Quick start

```python
from langchain_dataxapi import DataXAPIXiaohongshuNoteSearch

tool = DataXAPIXiaohongshuNoteSearch()
print(tool.invoke({"query": "露营", "sort": "popular"}))
```

The answer is a JSON string:

```json
{
  "endpoint": "xiaohongshu.notes.search",
  "data": {"items": [{"id": "…", "title": "…", "author": {"…": "…"}, "metrics": {"likes": 1024, "…": "…"}}]},
  "page": {"next_cursor": "…", "has_more": true},
  "billing": {"amount": "0.02", "currency": "USD", "balance_after": "9.98"},
  "request_id": "…"
}
```

For the next page, call again with `cursor` set to `page.next_cursor`; each page is charged on its own.

## Use in an agent

`create_agent` builds a LangGraph agent. Give it the whole toolkit:

```python
from langchain.agents import create_agent
from langchain_dataxapi import DataXAPIToolkit

tools = DataXAPIToolkit().get_tools()
agent = create_agent(
    model="claude-sonnet-4-6",
    tools=tools,
    system_prompt="You research Chinese and global social media with the DataXAPI tools. Cite links.",
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What do people on Xiaohongshu and Douyin say about camping coffee gear this week? "
                "Pick the three most liked posts and summarize their top comments.",
            }
        ]
    }
)
print(result["messages"][-1].content)
```

The agent searches with `dataxapi_xiaohongshu_notes_search` and `dataxapi_douyin_videos_search`, then reads comments with `dataxapi_xiaohongshu_notes_comments_list` and `dataxapi_douyin_videos_comments_list`. For anything without a named tool (a Bilibili user's profile, Weibo hot searches, Zhihu answers), it describes the need to `dataxapi_find`, gets the endpoint ID and parameters, and calls it with `dataxapi_call`.

To keep the tool list short, give the agent only the two general tools:

```python
tools = DataXAPIToolkit(endpoint_tools=False).get_tools()  # dataxapi_find and dataxapi_call
```

A runnable script is in [examples/agent.py](examples/agent.py).

## Tools

<!-- tools:start -->
| Tool | Class | What it returns | Price |
|---|---|---|---|
| `dataxapi_find` | `DataXAPIFind` | Endpoints for a need described in plain words, with price and parameters | free |
| `dataxapi_call` | `DataXAPICall` | Any DataXAPI endpoint by its ID | that endpoint's price |
| `dataxapi_xiaohongshu_notes_search` | `DataXAPIXiaohongshuNoteSearch` | Search Xiaohongshu notes by terms: title, text, author, engagement counts, images, and a link that opens | $0.02 per call |
| `dataxapi_douyin_videos_search` | `DataXAPIDouyinVideoSearch` | Search Douyin videos by terms, a page at a time, sorted by relevance, newest or most liked and filtered by time posted: caption, author with follower count, engagement counts | $0.02 per call |
| `dataxapi_wechat_mp_accounts_articles_list` | `DataXAPIWeChatOfficialAccountArticles` | Get a page of the articles a WeChat Official Account published, newest first: title, digest, link, time published | $0.02 per call |
| `dataxapi_douyin_videos_comments_list` | `DataXAPIDouyinVideoComments` | Get a page of comments on a Douyin video: text, commenter, likes, reply count, time posted | $0.002 per call |
| `dataxapi_douyin_videos_metrics` | `DataXAPIDouyinVideoMetrics` | Get a Douyin video's counts as of now, by its ID: plays and likes | $0.002 per call |
| `dataxapi_wechat_mp_articles_get` | `DataXAPIWeChatArticle` | Get one WeChat Official Account article by its link: title, text, time published, the account's name and IDs | $0.02 per call |
| `dataxapi_douyin_index_keywords_history` | `DataXAPIDouyinKeywordTrend` | Get the day-by-day search index and composite index of a keyword, or of one to five keywords at once, on Douyin over a date range, from the Douyin index, with the daily averages of the period, of the one before and of a year earlier | $0.006 per call |
| `dataxapi_wechat_posts_search` | `DataXAPIWeChatSearch` | Get a page of WeChat Search results for search terms: Official Account articles and Channels videos mixed, each saying in type whether it is an article or a video; by relevance, newest or hottest, filtered by time posted, or articles only or videos only: title or description, the source account's name, time published, an article's link (with a band of reads on some), a video's likes and saves | $0.02 per call |
| `dataxapi_wechat_channels_videos_search` | `DataXAPIWeChatChannelsVideoSearch` | Get a page of WeChat Channels videos for search terms through WeChat Search, by relevance, newest or hottest, filtered by time posted: description, the account's name and avatar, time published, likes and saves, length, cover | $0.02 per call |
| `dataxapi_xiaohongshu_notes_comments_list` | `DataXAPIXiaohongshuNoteComments` | Get a page of top-level comments on a Xiaohongshu note by ID or link, newest first or hottest first: text, commenter, likes, reply count, time posted | $0.02 per call |
| `dataxapi_tiktok_videos_search` | `DataXAPITikTokVideoSearch` | Search TikTok videos by keyword, 30 a page; sort by relevance, likes or time posted, and limit how recently they were posted | $0.002 per call |
| `dataxapi_youtube_videos_transcript_get` | `DataXAPIYouTubeTranscript` | Get the transcript of a YouTube video by ID or link: the whole text and timed segments | $0.002 per call |
<!-- tools:end -->

Live prices are on each endpoint's page at [dataxapi.com/apis](https://dataxapi.com/apis/?ref=langchain).

### Find and call any endpoint

```python
from langchain_dataxapi import DataXAPICall, DataXAPIFind

DataXAPIFind().invoke({"query": "bilibili user profile"})
# {"matches": [{"endpoint": "bilibili.users.get", "price_usd": "0.002", "example_params": {...}, ...}], ...}

DataXAPICall().invoke({"endpoint": "bilibili.users.get", "params": {"id": "8047632"}})
```

`params` may be an object or a JSON string. Lists such as `keywords` are sent as a JSON body.

### Errors

An error comes back as the tool's answer, so an agent can read it and correct itself, for example:

```text
DataXAPI error invalid_params: A parameter is invalid. Nothing was charged. Fix the request before trying again. Request ID: ….
```

It names the error code, whether anything was charged and whether to retry. Pass `handle_tool_error=False` to raise `ToolException` instead. Error codes: [dataxapi.com/docs](https://dataxapi.com/docs/?ref=langchain).

### Async

Every tool supports `ainvoke`:

```python
await DataXAPIDouyinVideoSearch().ainvoke({"query": "露营"})
```

## Development

```bash
uv sync --all-groups
make test              # unit tests, HTTP mocked, network off; includes langchain-tests' ToolsUnitTests
make integration_test  # live and free: dataxapi_find only. Paid tests need DATAXAPI_API_KEY and DATAXAPI_RUN_PAID=1
make generate          # rewrite the endpoint tools and the tables from the live catalog
make lint
```

The endpoint tools in `langchain_dataxapi/endpoint_tools.py` are written by `scripts/generate_tools.py` from the free catalog at <https://api.dataxapi.com/v1/catalog>: names, argument schemas, allowed values and prices. Do not edit that file by hand.

## 中文说明

`langchain-dataxapi` 让 LangChain、LangGraph 智能体直接取抖音、小红书、微信公众号、视频号、微信搜一搜、微博、B 站、知乎、快手、巨量算数，以及 TikTok、YouTube、X、Reddit 的公开数据。

- 一个 Key 调全部 237 个接口：12 个常用接口各有现成工具，另有免费的“找接口”（`dataxapi_find`）和“调用任意接口”（`dataxapi_call`）。
- 不用登录你自己的平台账号，不要 Cookie、不扫码。
- 按次计费，出错不收费；每个工具的说明写了价格，每次返回都带这次花了多少（`billing.amount`，美元）。
- 免费试用最多 333 次，不用绑卡；最低充 $10，余额不过期。

安装与设置：

```bash
pip install -U langchain-dataxapi
export DATAXAPI_API_KEY="dx_..."   # 在 https://dataxapi.com/console/keys/ 创建
```

```python
from langchain.agents import create_agent
from langchain_dataxapi import DataXAPIToolkit

agent = create_agent(model="claude-sonnet-4-6", tools=DataXAPIToolkit().get_tools())
question = "这周小红书上关于露营咖啡的笔记里，点赞最多的三篇讲了什么？评论区怎么说？"
agent.invoke({"messages": [{"role": "user", "content": question}]})
```

<!-- tools-zh:start -->
| 工具 | 类名 | 拿到什么 | 价格 |
|---|---|---|---|
| `dataxapi_find` | `DataXAPIFind` | 用一句话描述要的数据，列出能用的接口、价格和参数 | 免费 |
| `dataxapi_call` | `DataXAPICall` | 用接口编号加参数调用全部接口里的任何一个 | 按该接口的价格 |
| `dataxapi_xiaohongshu_notes_search` | `DataXAPIXiaohongshuNoteSearch` | 小红书笔记搜索 | $0.02 一次，出错不收费 |
| `dataxapi_douyin_videos_search` | `DataXAPIDouyinVideoSearch` | 抖音视频搜索 | $0.02 一次，出错不收费 |
| `dataxapi_wechat_mp_accounts_articles_list` | `DataXAPIWeChatOfficialAccountArticles` | 微信公众号文章列表 | $0.02 一次，出错不收费 |
| `dataxapi_douyin_videos_comments_list` | `DataXAPIDouyinVideoComments` | 抖音视频评论 | $0.002 一次，出错不收费 |
| `dataxapi_douyin_videos_metrics` | `DataXAPIDouyinVideoMetrics` | 抖音视频播放量 | $0.002 一次，出错不收费 |
| `dataxapi_wechat_mp_articles_get` | `DataXAPIWeChatArticle` | 微信公众号文章详情 | $0.02 一次，出错不收费 |
| `dataxapi_douyin_index_keywords_history` | `DataXAPIDouyinKeywordTrend` | 抖音巨量算数关键词热度趋势 | $0.006 一次，出错不收费 |
| `dataxapi_wechat_posts_search` | `DataXAPIWeChatSearch` | 微信搜一搜综合搜索 | $0.02 一次，出错不收费 |
| `dataxapi_wechat_channels_videos_search` | `DataXAPIWeChatChannelsVideoSearch` | 微信搜一搜视频号视频搜索 | $0.02 一次，出错不收费 |
| `dataxapi_xiaohongshu_notes_comments_list` | `DataXAPIXiaohongshuNoteComments` | 小红书笔记评论 | $0.02 一次，出错不收费 |
| `dataxapi_tiktok_videos_search` | `DataXAPITikTokVideoSearch` | TikTok 视频搜索 | $0.002 一次，出错不收费 |
| `dataxapi_youtube_videos_transcript_get` | `DataXAPIYouTubeTranscript` | YouTube 视频字幕 | $0.002 一次，出错不收费 |
<!-- tools-zh:end -->

翻页：把上一次返回的 `page.next_cursor` 作为 `cursor` 再调一次，每页单独计费。出错时工具返回一段文字，写明错误码、有没有收费、要不要重试，智能体可以据此自己改正。

## Links

- Endpoints and prices: <https://dataxapi.com/apis/?ref=langchain>
- API docs: <https://dataxapi.com/docs/?ref=langchain>
- Catalog for AI tools: <https://dataxapi.com/llms-full.txt>
- Support: support@dataxapi.com

## License

MIT
