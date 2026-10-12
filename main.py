from contextlib import asynccontextmanager
import os
from langchain_core.messages import AIMessage, ToolMessage
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator
import logging
from fastapi import HTTPException
from agent import create_mcp_agent

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = None

    try:
        app.state.agent = await create_mcp_agent()
        logger.info("Agent initialized successfully")
    except Exception:
        logger.exception("Failed to initialize MCP agent")

    yield

    app.state.agent = None


app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)
    session_id: str = Field(min_length=1, max_length=128)

    @field_validator("query", "session_id")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

class ChatResponse(BaseModel):
    response: str

def extract_final_text(result: object) -> str:
    if not isinstance(result, dict):
        raise ValueError("Agent result must be a dictionary")

    messages = result.get("messages")

    if not isinstance(messages, list) or not messages:
        raise ValueError("Agent result contains no messages")

    final_message = messages[-1]

    if not isinstance(final_message, AIMessage):
        raise ValueError("Agent result does not end with an AI message")

    if final_message.tool_calls:
        raise ValueError("Agent result ends with pending tool calls")

    content = final_message.content

    if isinstance(content, str):
        text = content

    elif isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)

            elif (
                isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ):
                parts.append(block["text"])

        text = "\n".join(parts)

    else:
        raise ValueError("Unsupported final message content")

    if not text.strip():
        raise ValueError("Agent returned no final text")

    return text


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:

    if app.state.agent is None:
        raise HTTPException(
            status_code=503,
            detail="The agent is temporarily unavailable. Please try again."
        )
    
    try:
        result = await app.state.agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": request.query}
                ]
            },
            config={
                "configurable": {
                    "thread_id": request.session_id
                }
            }
        )

        for message in result["messages"]:
            if getattr(message, "tool_calls", None):
                for tool_call in message.tool_calls:
                    logger.info(
                        "TOOL CALLED: %s",
                        tool_call["name"]
                    )

            if isinstance(message, ToolMessage):
                logger.info(
                    "TOOL RESULT: %s | ERROR: %s",
                    message.name,
                    message.status == "error"
                )

                if os.getenv("DEBUG_TOOL_OUTPUT", "false").lower() == "true":
                    logger.info("TOOL OUTPUT: %s", str(message.content)[:500])

        return ChatResponse(response=extract_final_text(result))

    except Exception:
        logger.exception("Agent request failed")

        raise HTTPException(
            status_code=503,
            detail="The agent is temporarily unavailable. Please try again."
        )