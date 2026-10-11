from contextlib import asynccontextmanager
import os
from langchain_core.messages import ToolMessage
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator
import logging
from fastapi import HTTPException
from agent import create_mcp_agent

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.agent = await create_mcp_agent()
        logger.info("Agent initialized successfully")
    except Exception:
        logger.exception("Failed to initialize MCP agent")
        raise

    yield


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


@app.post("/chat")
async def chat(request: ChatRequest):
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

        return {
            "response": result["messages"][-1].content
        }

    except Exception:
        logger.exception("Agent request failed")

        raise HTTPException(
            status_code=503,
            detail="The agent is temporarily unavailable. Please try again."
        )