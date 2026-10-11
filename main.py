from contextlib import asynccontextmanager
from langchain_core.messages import ToolMessage
from fastapi import FastAPI
from pydantic import BaseModel

from agent import create_mcp_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = await create_mcp_agent()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    query: str
    session_id: str


@app.post("/chat")
async def chat(request: ChatRequest):
    result = await app.state.agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request.query
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": request.session_id
            }
        }
    )

    # Inspect the tool calls made during this request
    for message in result["messages"]:
        if getattr(message, "tool_calls", None):
            for tool_call in message.tool_calls:
                print(f"TOOL CALLED: {tool_call['name']}")
                print(f"ARGUMENTS: {tool_call['args']}")

    for message in result["messages"]:
        if isinstance(message, ToolMessage):
            print(f"TOOL RESULT ({message.name}):")
            print(str(message.content)[:1000])
            print(f"TOOL ERROR: {message.status == 'error'}")

    return {
        "response": result["messages"][-1].content
    }