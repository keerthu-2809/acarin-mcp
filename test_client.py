"""Quick local test: spawns server.py over stdio and asks the four questions."""
import asyncio
from pathlib import Path
from fastmcp import Client

QUESTIONS = [
    "tell abt acarin",
    "who is ceo of acariin",
    "How many employees acarin has",
    "products they have",
]


async def main():
    async with Client(Path("server.py")) as client:
        tools = await client.list_tools()
        print("Tools:", [t.name for t in tools])
        for q in QUESTIONS:
            result = await client.call_tool("ask_acarin", {"query": q})
            print(f"\nQ: {q}\nA: {result.content[0].text}")


asyncio.run(main())