"""A LangGraph agent that researches social media with the DataXAPI tools.

    pip install -U langchain-dataxapi "langchain[anthropic]"
    export DATAXAPI_API_KEY="dx_..." ANTHROPIC_API_KEY="..."
    python examples/agent.py "What are people saying about camping coffee gear on Xiaohongshu this week?"

Each DataXAPI call the agent makes is charged at that endpoint's price; errors are not charged.
"""

from __future__ import annotations

import sys

from langchain.agents import create_agent

from langchain_dataxapi import DataXAPIToolkit

SYSTEM = (
    "You research Chinese and global social media with the DataXAPI tools. Use a named tool when one fits; "
    "otherwise find the endpoint with dataxapi_find and call it with dataxapi_call. Fetch only the pages you "
    "need, and cite the links of the posts you quote."
)


def main() -> None:
    question = " ".join(sys.argv[1:]) or "这周小红书上关于露营咖啡的笔记里，点赞最多的三篇讲了什么？评论区怎么说？"
    agent = create_agent(model="claude-sonnet-4-6", tools=DataXAPIToolkit().get_tools(), system_prompt=SYSTEM)
    for step in agent.stream({"messages": [{"role": "user", "content": question}]}, stream_mode="values"):
        step["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()
