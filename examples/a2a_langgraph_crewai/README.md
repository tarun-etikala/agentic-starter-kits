# A2A: LangGraph ↔ CrewAI (JSON-RPC)

Minimal **Agent2Agent** demo: a **LangGraph** ReAct-style agent runs as an A2A HTTP server and calls a **CrewAI** agent on another A2A server via `a2a-sdk` (JSON-RPC), using an **OpenAI-compatible** LLM (e.g. Llama Stack: `BASE_URL` + `API_KEY` + `MODEL_ID`).

## Layout

| File | Role |
|------|------|
| `crew_a2a_server.py` | CrewAI specialist → `A2AStarletteApplication` (default port **9100**) |
| `langgraph_a2a_server.py` | LangGraph orchestrator + tool `ask_crew_specialist` → A2A client → Crew (default **9200**) |
| `a2a_reply.py` | Shared `send_a2a_text_message()` helper |
| `demo_client.py` | Example client → orchestrator (prints raw JSON-RPC result) |

## Setup

```bash
cd examples/a2a_langgraph_crewai
cp template.env .env
# Edit .env: BASE_URL, MODEL_ID, API_KEY for your Llama Stack (or OpenAI-compatible) endpoint
uv sync
```

If you still have `examples/a2a_mvp/` (e.g. with `.env` or `.venv`), copy `.env` into this folder, delete the old directory, and run `uv sync` again here.

## Run

**Terminal 1 — CrewAI A2A**

```bash
uv run python crew_a2a_server.py
```

**Terminal 2 — LangGraph A2A** (needs Crew up; uses `CREW_A2A_URL`)

```bash
uv run python langgraph_a2a_server.py
```

**Terminal 3 — smoke test**

```bash
uv run python demo_client.py "Summarize what the specialist says about microservices in one sentence."
```

Or pass any prompt as the first CLI argument.

## Environment

See `template.env`. Important:

- **`BASE_URL`** must be the **OpenAI-compatible API root including `/v1`** (e.g. `http://127.0.0.1:8321/v1`). If you omit `/v1` (e.g. only `http://127.0.0.1:8321`), the LangGraph server now auto-appends `/v1`; without that, calls hit `/chat/completions` instead of `/v1/chat/completions` and Llama Stack often returns **`404 {'detail': 'Not Found'}`**.

- **`CREW_A2A_PUBLIC_URL`** — URL embedded in the Crew **Agent Card** (how the orchestrator resolves JSON-RPC). For local dev, match `http://127.0.0.1:9100` (no trailing slash in the env value; servers add `/` on the card).
- **`CREW_A2A_URL`** — Same host the orchestrator uses to call the Crew server (default `http://127.0.0.1:9100`).
- **`LANGGRAPH_A2A_PUBLIC_URL`** — Card URL for the orchestrator (default `http://127.0.0.1:9200`).

If you bind Docker/K8s ports differently, set the `*_PUBLIC_URL` values to what **other pods** use to reach each agent.

## Notes

- **Scope (minimal demo)**: non-streaming `send_message`, no `cancel`, no extended agent card.
- `A2AClient` emits a **deprecation** warning; it is still the pattern used in official [a2a-samples](https://github.com/a2aproject/a2a-samples) `test_client.py`; warnings are filtered in `a2a_reply.py` / `demo_client.py`.
- Dependency overlap between **CrewAI** and **LangGraph** is pinned in `pyproject.toml`; if `uv sync` fails, try relaxing one stack in a fork or split into two venvs.

## References

- [A2A Python SDK](https://pypi.org/project/a2a-sdk/)
- [a2a-samples helloworld](https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/helloworld)
