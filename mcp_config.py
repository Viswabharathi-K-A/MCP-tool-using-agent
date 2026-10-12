import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging
from mcp.types import CallToolResult, TextContent
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"

logger = logging.getLogger("uvicorn.error")


def mcp_error(message: str) -> CallToolResult:
    return CallToolResult(
        isError=True,
        content=[
            TextContent(type="text", text=message)
        ]
    )

def normalize_mcp_result(
    server_name: str,
    result: object
) -> CallToolResult:
    if not isinstance(result, CallToolResult):
        return mcp_error(
            "The MCP server returned an unusable result."
        )

    return result

async def handle_mcp_execution(request, handler):
    try:
        result = await handler(request)

    except Exception as exc:
        logger.warning(
            "MCP operation failed: server=%s tool=%s exception_type=%s",
            request.server_name,
            request.name,
            type(exc).__name__
        )

        return mcp_error(
            "The requested tool operation failed or its server was unavailable."
        )

    result = normalize_mcp_result(request.server_name, result)

    logger.info(
        "MCP operation completed: server=%s tool=%s is_error=%s",
        request.server_name,
        request.name,
        result.isError
    )

    return result

mcp_client = MultiServerMCPClient(
    {
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                str(WORKSPACE_DIR)
            ]
        },
        "tavily": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "tavily-mcp@latest"
            ],
            "env": {
                **os.environ,
                "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", "")
            }
        },
        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                "-m",
                "mcp_weather_server"
            ]
        }
    },
    tool_interceptors=[handle_mcp_execution],
    handle_tool_errors=True
)