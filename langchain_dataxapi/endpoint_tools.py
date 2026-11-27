"""One LangChain tool per DataXAPI endpoint most used by DataXAPI's customers.

Written by scripts/generate_tools.py from catalog 0264e2d6dd4ff743, price book 23. Do not edit by hand:
run the script again.
"""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field

from langchain_dataxapi.tools import DataXAPIEndpointTool


class DataXAPIXiaohongshuNoteSearchInput(BaseModel):
    """Arguments of dataxapi_xiaohongshu_notes_search."""

    query: str = Field(description='Search terms. Example: "咖啡".')
    sort: Literal["relevance", "latest", "popular", "most_comments", "most_favorites"] | None = Field(
        default=None,
        description="Sort order: relevance, newest, most liked, most commented, most saved. Default: relevance.",
    )
    type: Literal["video", "image"] | None = Field(
        default=None, description="Video notes only (video) or image notes only (image); both when left out."
    )
    published_within: Literal["day", "week", "half_year"] | None = Field(
        default=None, description="Only those published in the last day, week or half year."
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIXiaohongshuNoteSearch(DataXAPIEndpointTool):
    """Xiaohongshu note search (xiaohongshu.notes.search).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIXiaohongshuNoteSearch

            tool = DataXAPIXiaohongshuNoteSearch()
            tool.invoke({"query": "咖啡"})
    """

    name: str = "dataxapi_xiaohongshu_notes_search"
    description: str = "Search Xiaohongshu notes by terms: title, text, author, engagement counts, images, and a link that opens. Each says whether it is a brand partnership note on record. By relevance, newest, most liked, most commented or most saved; video or image notes only; published in the last day, week or half year. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIXiaohongshuNoteSearchInput
    endpoint: ClassVar[str] = "xiaohongshu.notes.search"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {"query": "咖啡"}


class DataXAPIDouyinVideoSearchInput(BaseModel):
    """Arguments of dataxapi_douyin_videos_search."""

    query: str = Field(description='Search terms. Example: "露营".')
    sort: Literal["relevance", "latest", "popular"] | None = Field(
        default=None,
        description="Order: the platform's ranking, newest first, most liked first. Douyin does not serve most liked within a day; with that pair, a day's results come with each page in order of likes. Default: relevance.",
    )
    published_within: Literal["day", "week", "half_year"] | None = Field(
        default=None, description="Only videos posted within the last day, week or half year; any time when left out."
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIDouyinVideoSearch(DataXAPIEndpointTool):
    """Douyin video search (douyin.videos.search).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIDouyinVideoSearch

            tool = DataXAPIDouyinVideoSearch()
            tool.invoke({"query": "露营"})
    """

    name: str = "dataxapi_douyin_videos_search"
    description: str = "Search Douyin videos by terms, a page at a time, sorted by relevance, newest or most liked and filtered by time posted: caption, author with follower count, engagement counts. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIDouyinVideoSearchInput
    endpoint: ClassVar[str] = "douyin.videos.search"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {"query": "露营"}


class DataXAPIWeChatOfficialAccountArticlesInput(BaseModel):
    """Arguments of dataxapi_wechat_mp_accounts_articles_list."""

    id: str = Field(
        description="The account's original ID, mostly starting with gh_ but not always, not the account's name; knowing only the name, find it with wechat.accounts.search and take id. Example: \"gh_13c97ab93ce8\"."
    )
    tab: Literal["articles", "videos", "images"] | None = Field(
        default=None,
        description="Which tab of the account's page: articles (the default), videos or pictures. Default: articles.",
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIWeChatOfficialAccountArticles(DataXAPIEndpointTool):
    """WeChat Official Account articles (wechat_mp.accounts.articles.list).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIWeChatOfficialAccountArticles

            tool = DataXAPIWeChatOfficialAccountArticles()
            tool.invoke({"id": "gh_13c97ab93ce8"})
    """

    name: str = "dataxapi_wechat_mp_accounts_articles_list"
    description: str = "Get a page of the articles a WeChat Official Account published, newest first: title, digest, link, time published. Each also says whether it was the lead article or one below, its format and cover. The page's articles tab by default; its videos or pictures tab when asked. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIWeChatOfficialAccountArticlesInput
    endpoint: ClassVar[str] = "wechat_mp.accounts.articles.list"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {"id": "gh_13c97ab93ce8"}


class DataXAPIDouyinVideoCommentsInput(BaseModel):
    """Arguments of dataxapi_douyin_videos_comments_list."""

    id: str | None = Field(
        default=None,
        description='Video ID, a string of digits. With only a link or a share text, give it as url. Example: "7694940173372575014".',
    )
    url: str | None = Field(
        default=None,
        description='Link to the video, pasted as it is: the https://www.douyin.com/video/… web link, a web link with modal_id in it, the page a share opens on a phone, the v.douyin.com short link the app copies, or a whole share text with one of these in it. A short link is opened once to see which video it leads to. Example: "https://www.douyin.com/video/7694940173372575014".',
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIDouyinVideoComments(DataXAPIEndpointTool):
    """Douyin video comments (douyin.videos.comments.list).

    Price: $0.002 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIDouyinVideoComments

            tool = DataXAPIDouyinVideoComments()
            tool.invoke({"id": "7694940173372575014"})
    """

    name: str = "dataxapi_douyin_videos_comments_list"
    description: str = "Get a page of comments on a Douyin video: text, commenter, likes, reply count, time posted. Give one of: id, url. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.002 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIDouyinVideoCommentsInput
    endpoint: ClassVar[str] = "douyin.videos.comments.list"
    one_of: ClassVar[tuple[str, ...]] = ("id", "url")
    example: ClassVar[dict[str, Any]] = {"id": "7694940173372575014"}


class DataXAPIDouyinVideoMetricsInput(BaseModel):
    """Arguments of dataxapi_douyin_videos_metrics."""

    id: str | None = Field(
        default=None,
        description='Video ID, a string of digits. With only a link or a share text, give it as url. Example: "7694940173372575014".',
    )
    url: str | None = Field(
        default=None,
        description='Link to the video, pasted as it is: the https://www.douyin.com/video/… web link, a web link with modal_id in it, the page a share opens on a phone, the v.douyin.com short link the app copies, or a whole share text with one of these in it. A short link is opened once to see which video it leads to. Example: "https://www.douyin.com/video/7694940173372575014".',
    )


class DataXAPIDouyinVideoMetrics(DataXAPIEndpointTool):
    """Douyin video play count (douyin.videos.metrics).

    Price: $0.002 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIDouyinVideoMetrics

            tool = DataXAPIDouyinVideoMetrics()
            tool.invoke({"id": "7694940173372575014"})
    """

    name: str = "dataxapi_douyin_videos_metrics"
    description: str = "Get a Douyin video's counts as of now, by its ID: plays and likes. Give one of: id, url. Price: $0.002 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIDouyinVideoMetricsInput
    endpoint: ClassVar[str] = "douyin.videos.metrics"
    one_of: ClassVar[tuple[str, ...]] = ("id", "url")
    example: ClassVar[dict[str, Any]] = {"id": "7694940173372575014"}


class DataXAPIWeChatArticleInput(BaseModel):
    """Arguments of dataxapi_wechat_mp_articles_get."""

    url: str = Field(
        description='Link to the article, pasted as it is: the long link with __biz, mid, idx and sn, the short /s/ link, or a share text with one of them in it. Example: "https://mp.weixin.qq.com/s?__biz=MjM5MjAxNDM4MA==&mid=2667038683&idx=1&sn=0422127e651acd7f6cf6ef7e1cff04bc".'
    )


class DataXAPIWeChatArticle(DataXAPIEndpointTool):
    """WeChat Official Account article detail (wechat_mp.articles.get).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIWeChatArticle

            tool = DataXAPIWeChatArticle()
            tool.invoke({"url": "https://mp.weixin.qq.com/s?__biz=MjM5MjAxNDM4MA==&mid=2667038683&idx=1&sn=0422127e651acd7f6cf6ef7e1cff04bc"})
    """

    name: str = "dataxapi_wechat_mp_articles_get"
    description: str = "Get one WeChat Official Account article by its link: title, text, time published, the account's name and IDs. It also says whether it was the lead article or one below, its format, cover, digest, byline, \"read the original\" link and the IP location it was posted from. Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIWeChatArticleInput
    endpoint: ClassVar[str] = "wechat_mp.articles.get"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {
        "url": "https://mp.weixin.qq.com/s?__biz=MjM5MjAxNDM4MA==&mid=2667038683&idx=1&sn=0422127e651acd7f6cf6ef7e1cff04bc"
    }


class DataXAPIDouyinKeywordTrendInput(BaseModel):
    """Arguments of dataxapi_douyin_index_keywords_history."""

    keyword: str | None = Field(
        default=None,
        description='One keyword, at most 50 characters and without a comma; letter case does not matter. Example: "咖啡".',
    )
    keywords: list[str] | None = Field(
        default=None,
        description='One to five keywords, each at most 50 characters and without a comma; letter case does not matter. One item comes back per keyword that has figures; a keyword the index does not cover is not in the answer. Example: ["咖啡", "CityWalk"].',
    )
    since: str | None = Field(
        default=None,
        description='The first day wanted: the China-time (UTC+8) calendar day this moment falls on; 2026-09-01 means 1 September; left out, the 30 days that end on until. Example: "2026-09-01T00:00:00Z".',
    )
    until: str | None = Field(
        default=None,
        description='The last day wanted, read the same way. The platform publishes a day or two late: a day it has no figure for yet has a null index; left out, yesterday. Example: "2026-09-30T00:00:00Z".',
    )


class DataXAPIDouyinKeywordTrend(DataXAPIEndpointTool):
    """Douyin trend-index keyword trends (douyin.index.keywords.history).

    Price: $0.006 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIDouyinKeywordTrend

            tool = DataXAPIDouyinKeywordTrend()
            tool.invoke({"keyword": "咖啡"})
    """

    name: str = "dataxapi_douyin_index_keywords_history"
    description: str = "Get the day-by-day search index and composite index of a keyword, or of one to five keywords at once, on Douyin over a date range, from the Douyin index, with the daily averages of the period, of the one before and of a year earlier. An index is the platform's score of volume, not a count of searches; days are calendar days in China time (UTC+8). Give one of: keywords, keyword. Price: $0.006 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIDouyinKeywordTrendInput
    endpoint: ClassVar[str] = "douyin.index.keywords.history"
    one_of: ClassVar[tuple[str, ...]] = ("keywords", "keyword")
    example: ClassVar[dict[str, Any]] = {"keyword": "咖啡"}


class DataXAPIWeChatSearchInput(BaseModel):
    """Arguments of dataxapi_wechat_posts_search."""

    query: str = Field(description='Search terms. Example: "咖啡店开业".')
    sort: Literal["relevance", "latest", "popular"] | None = Field(
        default=None, description="By relevance, by time published (newest first) or by how hot. Default: relevance."
    )
    published_within: Literal["day", "week", "half_year"] | None = Field(
        default=None, description="Only those published in the last day, week or half year."
    )
    type: Literal["article", "video"] | None = Field(
        default=None,
        description="Official Account articles only (article) or Channels videos only (video); both mixed when left out.",
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIWeChatSearch(DataXAPIEndpointTool):
    """WeChat Search articles and videos (wechat.posts.search).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIWeChatSearch

            tool = DataXAPIWeChatSearch()
            tool.invoke({"query": "咖啡店开业"})
    """

    name: str = "dataxapi_wechat_posts_search"
    description: str = "Get a page of WeChat Search results for search terms: Official Account articles and Channels videos mixed, each saying in type whether it is an article or a video; by relevance, newest or hottest, filtered by time posted, or articles only or videos only: title or description, the source account's name, time published, an article's link (with a band of reads on some), a video's likes and saves. WeChat Search gives no account ID. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIWeChatSearchInput
    endpoint: ClassVar[str] = "wechat.posts.search"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {"query": "咖啡店开业"}


class DataXAPIWeChatChannelsVideoSearchInput(BaseModel):
    """Arguments of dataxapi_wechat_channels_videos_search."""

    query: str = Field(description='Search terms. Example: "露营装备推荐".')
    sort: Literal["relevance", "latest", "popular"] | None = Field(
        default=None, description="By relevance, by time published (newest first) or by how hot. Default: relevance."
    )
    published_within: Literal["day", "week", "half_year"] | None = Field(
        default=None, description="Only those published in the last day, week or half year."
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIWeChatChannelsVideoSearch(DataXAPIEndpointTool):
    """WeChat Channels video search (wechat_channels.videos.search).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIWeChatChannelsVideoSearch

            tool = DataXAPIWeChatChannelsVideoSearch()
            tool.invoke({"query": "露营装备推荐"})
    """

    name: str = "dataxapi_wechat_channels_videos_search"
    description: str = "Get a page of WeChat Channels videos for search terms through WeChat Search, by relevance, newest or hottest, filtered by time posted: description, the account's name and avatar, time published, likes and saves, length, cover. WeChat Search gives no account ID, and a video's ID is an encrypted one starting with export/: given as export_id to wechat_channels.videos.get it yields the numeric ID, the video file's address and the key that decrypts it; it expires, so use it soon. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIWeChatChannelsVideoSearchInput
    endpoint: ClassVar[str] = "wechat_channels.videos.search"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {"query": "露营装备推荐"}


class DataXAPIXiaohongshuNoteCommentsInput(BaseModel):
    """Arguments of dataxapi_xiaohongshu_notes_comments_list."""

    id: str | None = Field(
        default=None,
        description='Note ID, 24 hexadecimal characters. With only a link or a share text, give it as url. Example: "6a9c5884000000002b002d95".',
    )
    url: str | None = Field(
        default=None,
        description='Link to the note, pasted as it is: the https://www.xiaohongshu.com/explore/… address from the browser, the https://www.xiaohongshu.com/discovery/item/… link the website shares (query parameters such as xsec_token are fine), a whole share text with such a link in it, or the xhslink.com short link the app copies (alone or in its share text). A short link is opened once to see which note it leads to; where it cannot be, paste the note\'s full link or its ID. Example: "https://www.xiaohongshu.com/explore/6a9c5884000000002b002d95?xsec_token=ABx1y2z3".',
    )
    sort: Literal["latest", "popular"] | None = Field(
        default=None, description="Newest first (the default), or hottest first (most liked first). Default: latest."
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPIXiaohongshuNoteComments(DataXAPIEndpointTool):
    """Xiaohongshu note comments (xiaohongshu.notes.comments.list).

    Price: $0.02 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIXiaohongshuNoteComments

            tool = DataXAPIXiaohongshuNoteComments()
            tool.invoke({"id": "6a9c5884000000002b002d95"})
    """

    name: str = "dataxapi_xiaohongshu_notes_comments_list"
    description: str = "Get a page of top-level comments on a Xiaohongshu note by ID or link, newest first or hottest first: text, commenter, likes, reply count, time posted. Give one of: id, url. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.02 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIXiaohongshuNoteCommentsInput
    endpoint: ClassVar[str] = "xiaohongshu.notes.comments.list"
    one_of: ClassVar[tuple[str, ...]] = ("id", "url")
    example: ClassVar[dict[str, Any]] = {"id": "6a9c5884000000002b002d95"}


class DataXAPITikTokVideoSearchInput(BaseModel):
    """Arguments of dataxapi_tiktok_videos_search."""

    query: str = Field(description='Search terms. Example: "space station".')
    sort: Literal["relevance", "popular", "latest"] | None = Field(
        default=None, description="By relevance, by likes, or newest first. Default: relevance."
    )
    published_within: Literal["day", "week", "month", "half_year"] | None = Field(
        default=None, description="Only videos posted within this period."
    )
    cursor: str | None = Field(
        default=None,
        description="Leave out for the first page. For the next page, the page.next_cursor of the last answer, with the same other arguments; each page is charged on its own.",
    )


class DataXAPITikTokVideoSearch(DataXAPIEndpointTool):
    """TikTok video search (tiktok.videos.search).

    Price: $0.002 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPITikTokVideoSearch

            tool = DataXAPITikTokVideoSearch()
            tool.invoke({"query": "space station"})
    """

    name: str = "dataxapi_tiktok_videos_search"
    description: str = "Search TikTok videos by keyword, 30 a page; sort by relevance, likes or time posted, and limit how recently they were posted. One call returns one page; for the next, call again with cursor set to page.next_cursor (charged on its own). Price: $0.002 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPITikTokVideoSearchInput
    endpoint: ClassVar[str] = "tiktok.videos.search"
    one_of: ClassVar[tuple[str, ...]] = ()
    example: ClassVar[dict[str, Any]] = {"query": "space station"}


class DataXAPIYouTubeTranscriptInput(BaseModel):
    """Arguments of dataxapi_youtube_videos_transcript_get."""

    id: str | None = Field(default=None, description='Video ID. Example: "dQw4w9WgXcQ".')
    url: str | None = Field(
        default=None,
        description='Link to the video: a watch, shorts, embed, live or youtu.be link. Example: "https://www.youtube.com/watch?v=dQw4w9WgXcQ".',
    )
    lang: str | None = Field(
        default=None,
        description='Which language of captions to get, as a language code (en, es, ja, zh-Hans, say); left out, the captions of the video\'s own language come first. A video without captions in that language is answered as one without captions. Example: "en".',
    )


class DataXAPIYouTubeTranscript(DataXAPIEndpointTool):
    """YouTube video transcript (youtube.videos.transcript.get).

    Price: $0.002 per call; errors are not charged.

    Example:
        .. code-block:: python

            from langchain_dataxapi import DataXAPIYouTubeTranscript

            tool = DataXAPIYouTubeTranscript()
            tool.invoke({"id": "dQw4w9WgXcQ"})
    """

    name: str = "dataxapi_youtube_videos_transcript_get"
    description: str = "Get the transcript of a YouTube video by ID or link: the whole text and timed segments. lang chooses the language of the captions. Give one of: id, url. Price: $0.002 per call; errors are not charged. No sign-in to the user's own platform account is needed."
    args_schema: type[BaseModel] = DataXAPIYouTubeTranscriptInput
    endpoint: ClassVar[str] = "youtube.videos.transcript.get"
    one_of: ClassVar[tuple[str, ...]] = ("id", "url")
    example: ClassVar[dict[str, Any]] = {"id": "dQw4w9WgXcQ"}


ENDPOINT_TOOLS: tuple[type[DataXAPIEndpointTool], ...] = (
    DataXAPIXiaohongshuNoteSearch,
    DataXAPIDouyinVideoSearch,
    DataXAPIWeChatOfficialAccountArticles,
    DataXAPIDouyinVideoComments,
    DataXAPIDouyinVideoMetrics,
    DataXAPIWeChatArticle,
    DataXAPIDouyinKeywordTrend,
    DataXAPIWeChatSearch,
    DataXAPIWeChatChannelsVideoSearch,
    DataXAPIXiaohongshuNoteComments,
    DataXAPITikTokVideoSearch,
    DataXAPIYouTubeTranscript,
)
