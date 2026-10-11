import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"

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
    }
)