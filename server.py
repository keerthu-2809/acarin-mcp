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
import markdown
from starlette.responses import HTMLResponse, PlainTextResponse

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


DOCS_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Acarin Knowledge Connector - Documentation</title>
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 860px;
         margin: 0 auto; padding: 32px 20px; line-height: 1.6; color: #1f2328; }}
  h1, h2, h3 {{ line-height: 1.25; }} h2 {{ border-bottom: 1px solid #d0d7de; padding-bottom: 6px; margin-top: 40px; }}
  code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; font-size: 0.9em; }}
  pre {{ background: #f6f8fa; padding: 14px; border-radius: 8px; overflow-x: auto; }} pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; display: block; overflow-x: auto; }}
  th, td {{ border: 1px solid #d0d7de; padding: 8px 12px; text-align: left; vertical-align: top; }}
  th {{ background: #f6f8fa; }} a {{ color: #0969da; }} hr {{ border: 0; border-top: 1px solid #d0d7de; margin: 32px 0; }}
</style></head><body>{body}</body></html>"""


@mcp.custom_route("/docs", methods=["GET"])
async def docs(request: Request) -> HTMLResponse:
    """Public documentation page (README.md rendered as HTML) - use this as the listing's documentation URL."""
    md_text = (BASE_DIR / "README.md").read_text(encoding="utf-8")
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    return HTMLResponse(DOCS_TEMPLATE.format(body=body))


class BearerTokenAuth:
    """Optional: only active if MCP_AUTH_TOKEN is set.
    Rejects requests without 'Authorization: Bearer <token>' (except /health)."""

    def __init__(self, app, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") not in ("/health", "/docs"):
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
