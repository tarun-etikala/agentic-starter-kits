<div style="text-align: center;">

![OpenAI Logo](/images/openai_logo.svg)

# Responses Agent

</div>

---

## What this agent does

Minimal agent with no framework: only the OpenAI Python client and an Action/Observation loop with tools. Use with
OpenAI or any compatible API.

---

## Quick Start

```bash
cd agents/openai/responses_agent
make init        # creates .env from .env.example
vi .env          # fill in API_KEY, BASE_URL, MODEL_ID
make run         # starts on http://localhost:8080
```

## Configuration

### Local (with OpenAI API)

```
API_KEY=sk-...
BASE_URL=https://api.openai.com/v1
MODEL_ID=gpt-4o-mini
```

### Local (with Ollama + Llama Stack)

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
CONTAINER_IMAGE=quay.io/your-username/openai-responses-agent:latest
```

**Notes:**

- `API_KEY` - your API key or contact your cluster administrator
- `BASE_URL` - should end with `/v1`
- `MODEL_ID` - model identifier available on your endpoint
- `CONTAINER_IMAGE` - full image path (e.g. `quay.io/your-username/openai-responses-agent:latest`)

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
  -d '{"message": "How much does a Lenovo Laptop cost and what are the reviews?"}'
```

### POST /stream

```bash
curl -X POST http://localhost:8080/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "How much does a Lenovo Laptop cost and what are the reviews?"}'
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

- [OpenAI Python Client](https://github.com/openai/openai-python)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create)
