"""Test the server through its public ngrok URL (server must be running in http mode + ngrok)."""
import asyncio
import os

from dotenv import load_dotenv
from fastmcp import Client

load_dotenv()
URL = os.environ["MCP_URL"]  # e.g. https://your-name.ngrok-free.app/mcp
TOKEN = os.getenv("MCP_AUTH_TOKEN")


async def main():
    async with Client(URL, auth=TOKEN) as client:
        print("Tools:", [t.name for t in await client.list_tools()])
        result = await client.call_tool("ask_acarin", {"query": "who is ceo of acarin"})
        print(result.content[0].text)


asyncio.run(main())