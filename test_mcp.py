import asyncio
from mcp_config import mcp_client


async def main():
    tools = await mcp_client.get_tools()

    print(f"Discovered {len(tools)} tools:\n")

    for tool in tools:
        print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())