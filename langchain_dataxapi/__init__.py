"""LangChain tools for DataXAPI: social media and market data for agents.

``DataXAPIFind`` finds the endpoint for a need (free), ``DataXAPICall`` calls any endpoint by ID, and
one tool per popular endpoint calls it with typed arguments. ``DataXAPIToolkit`` gives them all.
"""

from importlib import metadata

from langchain_dataxapi._client import DataXAPIClient, DataXAPIError
from langchain_dataxapi.endpoint_tools import (
    ENDPOINT_TOOLS,
    DataXAPIDouyinKeywordTrend,
    DataXAPIDouyinVideoComments,
    DataXAPIDouyinVideoMetrics,
    DataXAPIDouyinVideoSearch,
    DataXAPITikTokVideoSearch,
    DataXAPIWeChatArticle,
    DataXAPIWeChatChannelsVideoSearch,
    DataXAPIWeChatOfficialAccountArticles,
    DataXAPIWeChatSearch,
    DataXAPIXiaohongshuNoteComments,
    DataXAPIXiaohongshuNoteSearch,
    DataXAPIYouTubeTranscript,
)
from langchain_dataxapi.toolkits import DataXAPIToolkit
from langchain_dataxapi.tools import DataXAPIBaseTool, DataXAPICall, DataXAPIEndpointTool, DataXAPIFind

try:
    __version__ = metadata.version("langchain-dataxapi")
except metadata.PackageNotFoundError:
    __version__ = ""

__all__ = [
    "ENDPOINT_TOOLS",
    "DataXAPIBaseTool",
    "DataXAPICall",
    "DataXAPIClient",
    "DataXAPIDouyinKeywordTrend",
    "DataXAPIDouyinVideoComments",
    "DataXAPIDouyinVideoMetrics",
    "DataXAPIDouyinVideoSearch",
    "DataXAPIEndpointTool",
    "DataXAPIError",
    "DataXAPIFind",
    "DataXAPITikTokVideoSearch",
    "DataXAPIToolkit",
    "DataXAPIWeChatArticle",
    "DataXAPIWeChatChannelsVideoSearch",
    "DataXAPIWeChatOfficialAccountArticles",
    "DataXAPIWeChatSearch",
    "DataXAPIXiaohongshuNoteComments",
    "DataXAPIXiaohongshuNoteSearch",
    "DataXAPIYouTubeTranscript",
    "__version__",
]
