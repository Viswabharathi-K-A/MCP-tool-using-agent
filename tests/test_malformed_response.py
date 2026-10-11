import asyncio
from unittest.mock import AsyncMock, patch

from agent import create_mcp_agent


async def main():
    # Simulate the MCP adapter rejecting a malformed server response.
    with patch(
        "agent.mcp_client.get_tools",
        new_callable=AsyncMock
    ) as mock_get_tools:

        mock_get_tools.side_effect = ValueError(
            "Invalid MCP response: malformed tool schema"
        )

        try:
            await create_mcp_agent()
            print("FAIL: Invalid response was accepted")

        except ValueError as error:
            print("PASS: Malformed MCP response was detected")
            print(f"Error: {error}")


if __name__ == "__main__":
    asyncio.run(main())