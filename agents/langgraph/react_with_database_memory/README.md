<div style="text-align: center;">

![LangGraph Logo](/images/langgraph_logo.svg)

# ReAct Agent with Database Memory

</div>

---

## What this agent does

ReAct agent with PostgreSQL-backed conversation memory for persistent, thread-based chat history.
Uses OpenAI-compatible APIs for LLM access and LangGraph's `PostgresSaver` checkpointer for persistence.
Built with LangGraph and LangChain.

---

## Quick Start

```bash
cd agents/langgraph/react_with_database_memory
make init        # creates .env from .env.example
vi .env          # fill in API_KEY, BASE_URL, MODEL_ID, POSTGRES_* vars
make run         # starts on http://localhost:8080
```

## Prerequisites

A PostgreSQL database is required. Quick setup with Docker:

```bash
docker run --name postgres-agent \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=agent_memory \
  -p 5432:5432 \
  -d postgres:16
```

## Configuration

### Local

```
API_KEY=not-needed
BASE_URL=http://localhost:8321/v1
MODEL_ID=ollama/llama3.2:3b
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agent_memory
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mypassword
```

See [Local Development](../../../docs/local-development.md) for Ollama + Llama Stack setup.

### OpenShift / Remote API

```
API_KEY=your-api-key-here
BASE_URL=https://your-model-endpoint.com/v1
MODEL_ID=llama-3.1-8b-instruct
CONTAINER_IMAGE=quay.io/your-username/langgraph-react-db-memory:latest
POSTGRES_HOST=your-postgres-host.com
POSTGRES_PORT=5432
POSTGRES_DB=agent_memory
POSTGRES_USER=produser
POSTGRES_PASSWORD=secure_password
```

**Notes:**

- `API_KEY` - your API key or contact your cluster administrator
- `BASE_URL` - should end with `/v1`
- `MODEL_ID` - model identifier available on your endpoint
- `CONTAINER_IMAGE` - full image path (e.g. `quay.io/your-username/langgraph-react-db-memory:latest`)
- `POSTGRES_HOST` - PostgreSQL database hostname
- `POSTGRES_DB` - Database name for storing conversation history
- `POSTGRES_USER` and `POSTGRES_PASSWORD` - Database credentials

## Running Locally

Install dependencies and run:

```bash
uv pip install -e ".[dev]"
make run
```

## Deploying to OpenShift

```bash
make build       # builds and pushes container image
make deploy      # deploys via Helm
```

See [OpenShift Deployment](../../../docs/openshift-deployment.md) for details.

## API Endpoints

### POST /chat

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "thread_id": "my-conversation-1"
  }'
```

Continue the conversation with the same `thread_id`:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What did we talk about?"}],
    "thread_id": "my-conversation-1"
  }'
```

### GET /health

```bash
curl http://localhost:8080/health
```

## Database Memory Features

- **Thread-based conversations** — each conversation has a unique `thread_id`
- **Persistent across restarts** — all messages stored in PostgreSQL
- **FIFO context window** — keeps last 5 messages in context (configurable in `agent.py`)
- **Auto-managed schema** — tables created automatically on first run

## Tests

```bash
make test
```

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
