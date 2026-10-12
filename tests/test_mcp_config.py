
import asyncio
from types import SimpleNamespace

from mcp.types import CallToolResult, TextContent
from mcp_config import handle_mcp_execution


def make_request():
    return SimpleNamespace(
        server_name="weather",
        name="test_tool"
    )


# ----------------------------------------
# Successful tool execution
# ----------------------------------------

def test_mcp_execution_success():
    request = make_request()

    async def successful_handler(request):
        return CallToolResult(
            isError=False,
            content=[
                TextContent(
                    type="text",
                    text="Weather is sunny"
                )
            ]
        )

    result = asyncio.run(
        handle_mcp_execution(request, successful_handler)
    )

    assert result.isError is False
    assert result.content[0].text == "Weather is sunny"


# ----------------------------------------
# Tool execution exception
# ----------------------------------------

def test_mcp_execution_failure():
    request = make_request()

    async def failing_handler(request):
        raise ConnectionError("Weather server unavailable")

    result = asyncio.run(
        handle_mcp_execution(request, failing_handler)
    )

    assert result.isError is True
    assert "failed" in result.content[0].text.lower()


# ----------------------------------------
# Invalid MCP result
# ----------------------------------------

def test_mcp_invalid_result():
    request = make_request()

    async def invalid_handler(request):
        return None

    result = asyncio.run(
        handle_mcp_execution(request, invalid_handler)
    )

    assert result.isError is True
    assert "unusable result" in result.content[0].text


# ----------------------------------------
# Existing MCP error result
# ----------------------------------------

def test_mcp_existing_error_result():
    request = make_request()

    async def error_handler(request):
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text="Weather API unavailable"
                )
            ]
        )

    result = asyncio.run(
        handle_mcp_execution(request, error_handler)
    )

    assert result.isError is True
    assert result.content[0].text == "Weather API unavailable"
