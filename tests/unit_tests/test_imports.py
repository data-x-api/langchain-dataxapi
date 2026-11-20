import langchain_dataxapi

EXPECTED = {
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
}


def test_all_imports() -> None:
    assert set(langchain_dataxapi.__all__) == EXPECTED
    for name in EXPECTED:
        assert hasattr(langchain_dataxapi, name)
