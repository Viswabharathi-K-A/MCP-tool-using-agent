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
        checkpointer=checkpointer,
        system_prompt="""
    You are a helpful assistant with access to MCP tools.

    Choose tools automatically based on the user's request.
    Do not call tools when they are unnecessary.

    When a tool returns an error:
    - Do not treat the error as valid information.
    - Explain that the requested operation could not be completed.
    - If another available tool can reasonably help, you may use it.
    - Never invent tool results or claim an operation succeeded when it failed.

    When a tool returns missing or unusable data:
    - Explain the limitation.
    - Do not fabricate missing information.
    """
    )

    return agent