from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from mcp_config import mcp_client
from llm import llm


async def create_mcp_agent():
    tools = await mcp_client.get_tools()

    checkpointer = InMemorySaver()

    agent = create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer
    )

    return agent