<div style="text-align: center;">

# A2A: LangGraph ↔ CrewAI

</div>

---

## What this agent does

An **A2A (Agent-to-Agent)** example: a **CrewAI** pod exposes an A2A JSON-RPC server, and a **LangGraph** pod acts as an orchestrator that calls the Crew specialist over HTTP/A2A inside the cluster (or locally). One container image is built from a single `Dockerfile`; **`A2A_ROLE`** in the pod (`crew` vs `langgraph`) selects which process runs.

---

### Preconditions

- Copy/rename the env template and set values for your environment
- Choose **local** or **RH OpenShift Cluster** and fill the needed values
- Run **`source ./init.sh`** so variables from `.env` are loaded into your shell (required before `./deploy.sh` on OpenShift)

Go to agent dir:

```bash
cd agents/a2a_langgraph_crewai
```

Rename the env file:

```bash
mv template.env .env
```

#### Local (no cluster)

Edit `.env` for local dev. You can use placeholders for images if you only run Python locally:

```
API_KEY=your-key-or-not-needed
BASE_URL=http://localhost:8321/v1
MODEL_ID=ollama/llama3.1:8b
CONTAINER_IMAGE=not-needed
CREW_A2A_PUBLIC_URL=http://127.0.0.1:9100
LANGGRAPH_A2A_PUBLIC_URL=http://127.0.0.1:9200
CREW_A2A_URL=http://127.0.0.1:9100
CREW_A2A_PORT=9100
LANGGRAPH_A2A_PORT=9200
```

#### OpenShift Cluster

Edit `.env` and fill in all required values:

```
API_KEY=your-api-key-here
BASE_URL=https://your-llama-stack.example.com/v1
MODEL_ID=your-model-id
CONTAINER_IMAGE=quay.io/your-org/a2a-langgraph-crewai:latest
```

For deploy, `CREW_A2A_PUBLIC_URL` / `LANGGRAPH_A2A_PUBLIC_URL` are set automatically from OpenShift Routes; local defaults in `template.env` are for running servers on your machine.

**Notes:**

- `API_KEY` — contact your cluster administrator or your LLM provider
- `BASE_URL` — must include `/v1` for OpenAI-compatible chat
- `MODEL_ID` — model id accepted by that endpoint
- `CONTAINER_IMAGE` — one registry path, same style as other agents (e.g. ending in `:latest`). `deploy.sh` strips the tag and pushes **the same image** to two refs (**`:crew`** and **`:langgraph`**) so each Deployment keeps a distinct pull URL; the binary is identical, roles differ via **`A2A_ROLE`** in the manifest. Optionally set `CONTAINER_IMAGE_CREW` and `CONTAINER_IMAGE_LANGGRAPH` instead (e.g. two Quay repos).

Create and activate a virtual environment (Python 3.12+) in this directory using [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.12
source .venv/bin/activate
```

(On Windows: `.venv\Scripts\activate`)

Make scripts executable:

```bash
chmod +x init.sh deploy.sh
```

Load values from `.env` into environment variables:

```bash
source ./init.sh
```

---

## Local run (no cluster)

```bash
uv sync
```

Use **two terminals** (after `source ./init.sh` in each, or export the same vars):

```bash
# Terminal 1
uv run python -m a2a_langgraph_crewai.crew_a2a_server

# Terminal 2
uv run python -m a2a_langgraph_crewai.langgraph_a2a_server
```

Default ports: **9100** (Crew), **9200** (LangGraph). Do not set `PORT` unless you mirror the container (`8080`).

### Playground (LangGraph orchestrator)

With the LangGraph server running (terminal 2), open **http://127.0.0.1:9200/** in a browser. The chat uses **A2A JSON-RPC** on **`POST /`** with **`message/send`** (request body = `SendMessageRequest`, same shape as the **curl** examples under **Deploying to OpenShift**). The right-hand panel shows the outgoing JSON and the raw JSON-RPC response. The server also exposes **`POST /chat/completions`** (OpenAI-style) for parity with other agents. For local `curl`, use `http://127.0.0.1:9200` instead of the OpenShift route host.

---

## Deploying to OpenShift

Log in to the cluster:

```bash
oc login -u "login" -p "password" https://your-cluster:6443
oc project <namespace>
```

Log in to your container registry (e.g. Quay):

```bash
docker login -u='login' -p='password' quay.io
```

Install **gettext** (`envsubst`) if needed (e.g. `brew install gettext` on macOS).

In the agent directory, load `.env` **in the same shell** you use for deploy:

```bash
cd agents/a2a_langgraph_crewai
source ./init.sh
./deploy.sh
```

`./deploy.sh` will:

1. Run **`docker buildx` twice** — push to **`CONTAINER_IMAGE_CREW`**, then **`CONTAINER_IMAGE_LANGGRAPH`** (same `Dockerfile`, same layers; the second run usually hits cache)
2. Create `Secret` `a2a-langgraph-crewai-secrets` with `API_KEY`
3. Remove prior Deployment/Service/Route for this stack (label `app.kubernetes.io/part-of=a2a-langgraph-crewai`)
4. Apply `Service` and `Route` for both agents
5. Read public hostnames from `oc get route` and set `CREW_A2A_PUBLIC_URL` / `LANGGRAPH_A2A_PUBLIC_URL` to `https://…`
6. Apply `Deployment` manifests with those URLs (Agent Card for external clients). The LangGraph pod uses in-cluster `CREW_A2A_URL=http://a2a-crew-agent:8080`

### HTTP examples (LangGraph route)

Use the **LangGraph** Route (`a2a-langgraph-agent`), not the Crew route. Routes terminate TLS at the edge; use **`https://`**.

Get the route hostname (replace **`<YOUR_ROUTE_URL>`** below with that host, e.g. `a2a-langgraph-agent-myproject.apps.example.com`):

```bash
oc get route a2a-langgraph-agent -o jsonpath='{.spec.host}'
```

**Agent card**

```bash
curl -sS "https://<YOUR_ROUTE_URL>/.well-known/agent-card.json"
```

**A2A JSON-RPC (`message/send` on `POST /`)**

Same protocol as the browser playground: JSON-RPC 2.0 body = `SendMessageRequest` (see [a2a-sdk](https://pypi.org/project/a2a-sdk/)). Use a unique `messageId` (e.g. 32 hex chars) per request. The example below uses a **single-line** `-d '…'` body (no `'` inside the user text, so bash quoting stays simple):

```bash
curl -sS -X POST "https://<YOUR_ROUTE_URL>/" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"kind":"text","text":"Use the web search tool to find the Red Hat encrypted string."}],"messageId":"0123456789abcdef0123456789abcdef"}},"id":"curl-req-1"}'
```

The response is JSON-RPC (`result` or `error`), not OpenAI chat format.

**OpenAI-style chat (`POST /chat/completions`)**

Also available for parity with other agents in this repo (non-streaming example):

```bash
curl -sS -X POST "https://<YOUR_ROUTE_URL>/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Use the web search tool to find the Red Hat encrypted string."}],"stream":false}'
```

### Operational notes

- **A2A LangGraph → Crew**: `a2a_reply.send_a2a_text_message` logs each real `message/send` at **INFO** (peer URL, JSON-RPC id, text length, short preview). For full request/response JSON as seen by the client, run the LangGraph pod with **`LOG_LEVEL=DEBUG`** (or set the logger `a2a_langgraph_crewai.a2a_reply` to DEBUG) and read **`oc logs`** for the orchestrator Deployment.
- **TLS**: Routes use `edge` termination (same pattern as other agents in this repo).
- **Secrets**: do not commit `.env`; `API_KEY` is stored in the Kubernetes `Secret`.
- **Resources**: tune limits in YAML if your LLM stack needs it.
- **Scaling**: MVP assumes **one replica** per Deployment; scaling out would need shared state for A2A tasks.
- **BASE_URL** must be reachable **from the pods** (cluster egress or in-cluster LLM service).

---

## Architecture (OpenShift)

| Resource | Role |
|----------|------|
| `Deployment` **a2a-crew-agent** | CrewAI + A2A server, port **8080** |
| `Deployment` **a2a-langgraph-agent** | LangGraph + tool → `CREW_A2A_URL` |
| `Service` + `Route` ×2 | HTTPS; hosts feed Agent Card URLs |
| Inside the cluster | `CREW_A2A_URL=http://a2a-crew-agent:8080` |

---

## Files

| File / directory | Description |
|------------------|-------------|
| `init.sh` | Load and validate `.env` (use `source ./init.sh`) |
| `src/a2a_langgraph_crewai/` | Python package |
| `src/a2a_langgraph_crewai/crew_a2a_server.py` | CrewAI A2A server |
| `src/a2a_langgraph_crewai/langgraph_a2a_server.py` | LangGraph A2A server (calls Crew); playground UI + OpenAI-style chat |
| `src/a2a_langgraph_crewai/playground/templates/index.html` | Playground (chat + JSON-RPC trace panel) |
| `src/a2a_langgraph_crewai/images/rh_logo.svg` | Logo for playground watermark |
| `src/a2a_langgraph_crewai/a2a_reply.py` | A2A client helper |
| `src/a2a_langgraph_crewai/custom_tool.py` | Dummy Web Search tool |
| `src/a2a_langgraph_crewai/demo_client.py` | Optional CLI JSON-RPC client (same `POST /` as playground and curl) |
| `Dockerfile` + `entrypoint.sh` | One image; `entrypoint.sh` reads `A2A_ROLE` |
| `k8s/*.yaml` | Deployment / Service / Route |
| `deploy.sh` | Build, push, apply (run after `source ./init.sh`) |

---

## References

- [A2A Python SDK](https://pypi.org/project/a2a-sdk/)
- Related patterns: `agents/crewai/websearch_agent/`, `agents/langgraph/react_agent/`
