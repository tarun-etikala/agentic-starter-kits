<div style="text-align: center;">

![LlamaIndex Logo](/images/llamaindex_logo.svg)

# WebSearch Agent

</div>

---

## What this agent does

Agent built on LlamaIndex that uses a web search tool to query the internet and use the results in its answers.

---

## Quick Start

```bash
cd agents/llamaindex/websearch_agent
make init        # creates .env from .env.example
vi .env          # fill in API_KEY, BASE_URL, MODEL_ID
make run         # starts on http://localhost:8080
```

## Configuration

### Local

```
API_KEY=not-needed
BASE_URL=http://localhost:8321/v1
MODEL_ID=ollama/llama3.2:3b
```

See [Local Development](../../../docs/local-development.md) for Ollama + Llama Stack setup.

### OpenShift / Remote API

```
API_KEY=your-api-key-here
BASE_URL=https://your-model-endpoint.com/v1
MODEL_ID=llama-3.1-8b-instruct
CONTAINER_IMAGE=quay.io/your-username/llamaindex-websearch-agent:latest
```

**Notes:**

- `API_KEY` - your API key or contact your cluster administrator
- `BASE_URL` - should end with `/v1`
- `MODEL_ID` - model identifier available on your endpoint
- `CONTAINER_IMAGE` - full image path (e.g. `quay.io/your-username/llamaindex-websearch-agent:latest`)

## Running Locally

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
  -d '{"message": "Which company is considered the best?"}'
```

### POST /stream

```bash
curl -X POST http://localhost:8080/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Which company is considered the best?"}'
```

### GET /health

```bash
curl http://localhost:8080/health
```

## Tests

```bash
make test
```

## Resources

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)
- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
