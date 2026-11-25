# Acarin Knowledge Connector (MCP)

Ask Claude questions about **Acarin**: what the company does, its leadership, team size, products, services and notable projects. Answers come only from Acarin's official, curated knowledge base, so Claude gives accurate company information instead of guessing.

- **Server URL:** `https://acarin-mcp.onrender.com/mcp`
- **Transport:** Streamable HTTP
- **Authentication:** None (the connector only serves public company information)
- **Publisher:** Acarin Inc — [acarin.net](https://www.acarin.net)

---

## What you can ask

| Topic | Example prompts |
|---|---|
| Company overview | "Tell me about Acarin." · "What does Acarin do?" |
| Leadership | "Who is the CEO of Acarin?" · "Who is Acarin's CTO?" |
| Team size | "How many employees does Acarin have?" |
| Products | "What products does Acarin offer?" · "What is MissionMind.ai?" |
| Services | "Does Acarin do cloud modernization?" · "What AI services does Acarin provide?" |
| Projects & clients | "What work has Acarin done for government agencies?" |
| Contact | "Where is Acarin headquartered?" · "How do I contact Acarin?" |

If a question is outside the knowledge base, the connector says it doesn't have that information rather than making something up.

---

## Connecting in Claude

1. In Claude, open **Settings → Connectors**.
2. Find **Acarin Knowledge** in the directory and click **Connect**.
   *(Before the directory listing is live: choose **Add custom connector** and paste the server URL above.)*
3. No sign-in is needed. Ask Claude any question about Acarin and it will use the connector automatically.

The connector also works in any other MCP client that supports Streamable HTTP. Point the client at the server URL; no headers or API keys are required.

---

## Tools

### `ask_acarin`

Answers a natural-language question about Acarin using the official knowledge base.

| | |
|---|---|
| **Title** | Ask about Acarin |
| **Annotations** | `readOnlyHint: true` — the tool never creates, changes or deletes any data |
| **Input** | `query` (string, required): the user's question, e.g. `"Who is the CEO of Acarin?"` |
| **Output** | A short plain-text answer drawn from the knowledge base |

Example call:

```json
{ "name": "ask_acarin", "arguments": { "query": "What products does Acarin have?" } }
```

Example response:

```text
Acarin offers MissionMind.ai (an enterprise digital-workers platform), EvloTime (timesheet
management), HiPAI (a mobile electronic health records app) and HDMS (a health data
management system).
```

---

## Data and privacy

- **What is sent:** only the question text that Claude passes to the `ask_acarin` tool. No account details, files or conversation history are sent.
- **How it is processed:** the question and the Acarin knowledge base are sent to a third-party LLM provider ([Groq](https://groq.com)) to generate the answer.
- **What is stored:** the connector does not store questions or answers. Standard hosting logs (request time, status code) may be kept by the hosting provider for operations and security.
- **No personal data is needed.** Please don't include personal or confidential information in questions.

Full privacy policy: `https://www.acarin.net/privacy.html`

---

## Limitations

- Answers cover only what is in Acarin's knowledge base. Information may lag behind very recent company changes.
- The employee figure is a range from a third-party company profile, not an exact headcount.
- The connector answers questions; it cannot take actions (contact Acarin, book meetings, etc.).

---

## Support

- **Email:** `info@acarin.net`
- **Website:** [acarin.net](https://www.acarin.net)
- **Issues:** open an issue in this repository

---

## For developers

### Run locally

```bash
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env  — then add your keys
python test_client.py
```

### Configuration (environment variables)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | API key from console.groq.com |
| `LLM_MODEL` | Yes | Groq chat model name |
| `LLM_BASE_URL` | No | OpenAI-compatible endpoint (default: Groq) |
| `MCP_TRANSPORT` | No | `stdio` (default locally) or `http` (set in Docker) |
| `PORT` | No | HTTP port (default `8000`; set automatically on Render) |
| `MCP_AUTH_TOKEN` | No | If set, requires `Authorization: Bearer <token>` |

### Deploy with Docker

```bash
docker build -t acarin-mcp .
docker run -p 8000:8000 -e GROQ_API_KEY=... -e LLM_MODEL=... acarin-mcp
```

Health check: `GET /health` returns `ok`.

### Updating the knowledge base

Edit `knowledge_base.md`, commit and push. Render redeploys automatically.

---

## Changelog

- **1.0.0** — Initial release: `ask_acarin` tool with company, leadership, team, products, services and projects coverage.
