"""
Acarin Knowledge MCP Server
Answers questions about Acarin using a local knowledge base + a free LLM API (Groq).

Config comes from environment variables:
  - Locally: from a .env file (optional)
  - On Render: from the service's Environment settings
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from openai import OpenAI
from starlette.requests import Request
from starlette.responses import PlainTextResponse

load_dotenv()  # no-op when there is no .env file (e.g. on Render)

BASE_DIR = Path(__file__).parent
KB_PATH = Path(os.getenv("KB_PATH", BASE_DIR / "knowledge_base.md"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to .env locally or to Render's Environment settings.")

MODEL = os.getenv("LLM_MODEL")
if not MODEL:
    raise RuntimeError("LLM_MODEL is not set. Use a model name from your Groq models list.")

# Groq exposes an OpenAI-compatible API, so the openai SDK works with a different base_url.
llm = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
)

SYSTEM_PROMPT = """You are Acarin's company assistant.
Answer ONLY using the knowledge base below. If the answer is not in it,
say "I don't have that information about Acarin." Do not guess.
Users may misspell the company name (e.g. "acariin") - treat it as Acarin.
Keep answers short and factual.

<knowledge_base>
{kb}
</knowledge_base>"""

mcp = FastMCP("acarin-knowledge")


def load_kb() -> str:
    # Re-read on every call so edits to the file apply without restarting.
    return KB_PATH.read_text(encoding="utf-8")


@mcp.tool(annotations={"title": "Ask about Acarin", "readOnlyHint": True})
def ask_acarin(query: str) -> str:
    """Answer any question about Acarin: company overview, CEO and leadership,
    employee count, products and services. Pass the user's question as-is."""
    resp = llm.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(kb=load_kb())},
            {"role": "user", "content": query},
        ],
    )
    return resp.choices[0].message.content


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> PlainTextResponse:
    """Health check for Render (and a quick browser check that the server is up)."""
    return PlainTextResponse("ok")


class BearerTokenAuth:
    """Optional: only active if MCP_AUTH_TOKEN is set.
    Rejects requests without 'Authorization: Bearer <token>' (except /health)."""

    def __init__(self, app, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") != "/health":
            headers = dict(scope["headers"])
            if headers.get(b"authorization") != self.expected:
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"text/plain")]})
                await send({"type": "http.response.body", "body": b"Unauthorized"})
                return
        await self.app(scope, receive, send)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        import uvicorn

        app = mcp.http_app(path="/mcp")
        token = os.getenv("MCP_AUTH_TOKEN")
        if token:
            app = BearerTokenAuth(app, token)
        # Render provides PORT; 0.0.0.0 is required so traffic from outside the container reaches us.
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))
        print(f"MCP server on http://{host}:{port}/mcp")
        uvicorn.run(app, host=host, port=port)
    else:
        mcp.run()