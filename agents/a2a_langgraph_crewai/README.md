# A2A: LangGraph ↔ CrewAI (JSON-RPC) — agent template

This directory is an **agent template** in the same style as other templates under `agents/` (Dockerfile, `k8s/`, `deploy.sh`). You can **deploy it to OpenShift** as **two Deployments**: Crew (A2A specialist) and LangGraph (A2A orchestrator calling Crew over HTTP/A2A inside the cluster).

## Architecture (OpenShift)

| Resource | Role |
|----------|------|
| `Deployment` **a2a-crew-agent** | CrewAI + `A2AStarletteApplication`, port **8080** |
| `Deployment` **a2a-langgraph-agent** | LangGraph + `ask_crew_specialist` tool → `CREW_A2A_URL` |
| `Service` + `Route` ×2 | HTTPS at the edge; hosts feed **Agent Card** URLs (`CREW_A2A_PUBLIC_URL`, `LANGGRAPH_A2A_PUBLIC_URL`) |
| Inside the cluster | `CREW_A2A_URL=http://a2a-crew-agent:8080` (service DNS) |

Images are built from a **single** `Dockerfile` with `A2A_ROLE=crew` or `langgraph`.

## Local requirements (dev)

- Python **3.12+**, **uv**
- Access to an OpenAI-compatible LLM (`BASE_URL` with `/v1`, `MODEL_ID`, `API_KEY`)

## Local run (no cluster)

```bash
cd agents/a2a_langgraph_crewai
cp template.env .env
# Fill in .env
uv sync

# Terminal 1
uv run python crew_a2a_server.py

# Terminal 2
uv run python langgraph_a2a_server.py

# Terminal 3
uv run python demo_client.py "Your question here"
```

Locally the default ports are **9100** (Crew) and **9200** (LangGraph). **Do not** set `PORT` unless you are testing like in the container (`8080`).

## Deploying to OpenShift

### Preparation

1. `oc login …`, select project: `oc project <namespace>`
2. Copy `template.env` → `.env` and fill in:
   - `API_KEY`, `BASE_URL`, `MODEL_ID` — same LLM for both pods
   - `CONTAINER_IMAGE_CREW`, `CONTAINER_IMAGE_LANGGRAPH` — full image references in your registry (e.g. Quay), **different** tags (e.g. `:crew` and `:langgraph`)
3. Log in to the registry and configure `docker`/`podman` for `docker buildx … --push`
4. Install **gettext** (`envsubst`) if missing: `brew install gettext` (macOS)

### Script

```bash
./deploy.sh
```

The script:

1. Builds and pushes **two** images (`--build-arg A2A_ROLE=…`)
2. Creates `Secret` `a2a-langgraph-crewai-secrets` with `API_KEY`
3. Applies `Service` and `Route` for both agents
4. Reads **public hostnames** from `oc get route …` and sets `CREW_A2A_PUBLIC_URL` / `LANGGRAPH_A2A_PUBLIC_URL` to `https://…`
5. Applies `Deployment` with those URLs (Agent Card for external clients)
6. The orchestrator pod uses **internal** `CREW_A2A_URL=http://a2a-crew-agent:8080`

### Test from your laptop (demo client)

After deployment:

```bash
export LANGGRAPH_A2A_PUBLIC_URL="https://$(oc get route a2a-langgraph-agent -o jsonpath='{.spec.host}')"
uv run python demo_client.py "Test question"
```

### Operational notes

- **TLS**: Route with `edge` termination (same pattern as other agents in this repo).
- **Secrets**: do not commit `.env`; `API_KEY` only in Kubernetes `Secret`.
- **Resources**: tune limits in YAML for vLLM / Llama Stack as needed.
- **Scaling**: the MVP assumes **1 replica** per Deployment (in-memory A2A state); horizontal scaling would need a shared task store, etc.
- **BASE_URL** must be reachable **from the pods** (e.g. public Llama Stack endpoint or an in-cluster service).

## Files

| File / directory | Description |
|------------------|-------------|
| `crew_a2a_server.py` | CrewAI A2A server |
| `langgraph_a2a_server.py` | LangGraph A2A server (A2A client → Crew) |
| `a2a_reply.py` | A2A client helper |
| `demo_client.py` | JSON-RPC example against the orchestrator |
| `Dockerfile` + `entrypoint.sh` | Image with `A2A_ROLE` |
| `k8s/*.yaml` | Deployment / Service / Route |
| `deploy.sh` | Build + apply |

## References

- [A2A Python SDK](https://pypi.org/project/a2a-sdk/)
- Other agents in this repo: `agents/crewai/websearch_agent/`, `agents/langgraph/react_agent/` (OpenShift patterns)
