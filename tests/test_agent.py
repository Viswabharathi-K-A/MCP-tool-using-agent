import asyncio
from unittest.mock import AsyncMock

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

import agent


class ScriptedModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_sequential_tools_and_session_memory(monkeypatch):
    calls = []

    @tool
    def read_file(path: str) -> str:
        """Read a file from the workspace."""
        calls.append(("read", path))
        return "MCP protocol"

    @tool
    def search(query: str) -> str:
        """Search for information about a topic."""
        calls.append(("search", query))
        return "MCP connects tools to agents."

    model = ScriptedModel(responses=[
        AIMessage(content="", tool_calls=[
            {"name": "read_file", "args": {"path": "notes.txt"}, "id": "read-1"}
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "search", "args": {"query": "MCP protocol"}, "id": "search-1"}
        ]),
        AIMessage(content="MCP connects tools to agents."),
        AIMessage(content="You asked about notes.txt."),
        AIMessage(content="Hello"),
    ])
    monkeypatch.setattr(agent, "llm", model)
    discovery = AsyncMock(return_value=[read_file, search])
    monkeypatch.setattr(agent.mcp_client, "get_tools", discovery)

    async def run():
        graph = await agent.create_mcp_agent()
        config = {"configurable": {"thread_id": "session-a"}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="Read notes.txt, then research its topic.")]},
            config=config,
        )
        assert calls == [("read", "notes.txt"), ("search", "MCP protocol")]
        assert len([m for m in result["messages"] if isinstance(m, ToolMessage)]) == 2
        assert result["messages"][-1].content == "MCP connects tools to agents."
        followup = await graph.ainvoke(
            {"messages": [HumanMessage(content="What did I ask?")]}, config=config
        )
        assert [m.content for m in followup["messages"] if isinstance(m, HumanMessage)] == [
            "Read notes.txt, then research its topic.", "What did I ask?"
        ]
        separate = await graph.ainvoke(
            {"messages": [HumanMessage(content="Hello")]},
            config={"configurable": {"thread_id": "session-b"}},
        )
        assert len(separate["messages"]) == 2
        assert calls == [("read", "notes.txt"), ("search", "MCP protocol")]

    asyncio.run(run())
    discovery.assert_awaited_once()
