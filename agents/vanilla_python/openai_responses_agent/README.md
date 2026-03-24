<div style="text-align: center;">

![OpenAI Logo](/images/openai_logo.svg)

# Pure Responses Agent

</div>

---

## What this agent does

Minimal agent with no framework: only the OpenAI Python client and an Action/Observation loop with tools. Use with
OpenAI or any compatible API.

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Podman](https://podman.io/) or [Docker](https://www.docker.com/) — for local container builds (Option A)
- [oc](https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html) — for OpenShift deployment
- [Helm](https://helm.sh/) — for deploying to Kubernetes/OpenShift

## Quick Start

```bash
cd agents/vanilla_python/openai_responses_agent
make init        # creates .env from .env.example
# Edit .env with your API_KEY, BASE_URL, MODEL_ID
make run         # starts web playground UI on http://localhost:8000
make run-cli     # interactive terminal chat (no web server)
```

## Configuration

### Local (with Ollama + Llama Stack)

```
API_KEY=not-needed
BASE_URL=http://localhost:8321/v1
MODEL_ID=ollama/llama3.2:3b
```

### Local (with OpenAI API)

```
API_KEY=sk-...
BASE_URL=https://api.openai.com/v1
MODEL_ID=gpt-4o-mini
```

See [Local Development](../../../docs/local-development.md) for Ollama + Llama Stack setup for local model serving.

### OpenShift / Remote API

```
API_KEY=your-api-key-here
BASE_URL=https://your-llama-stack-distribution.com/v1
MODEL_ID=llama-3.1-8b-instruct
CONTAINER_IMAGE=quay.io/your-username/openai-responses-agent:latest
```

**Notes:**

- `API_KEY` - your API key or contact your cluster administrator
- `BASE_URL` - should end with `/v1`
- `MODEL_ID` - model identifier available on your endpoint
- `CONTAINER_IMAGE` – full image path where the agent container will be pushed and pulled from. The image is built
  locally, pushed to this registry, and then deployed to OpenShift.

  Format: `<registry>/<namespace>/<image-name>:<tag>`

  Examples:

    - Quay.io: `quay.io/your-username/openai-responses-agent:latest`
    - Docker Hub: `docker.io/your-username/openai-responses-agent:latest`
    - GHCR: `ghcr.io/your-org/openai-responses-agent:latest`

## Deploying to OpenShift

```bash
# Option A: Build locally with Podman (or Docker) and push to a registry
make build            # builds container image locally
make push             # pushes image to registry
make deploy           # deploys via Helm

# Option B: Build in-cluster on OpenShift (no Podman/Docker needed)
make build-openshift  # builds image via OpenShift BuildConfig
# Set CONTAINER_IMAGE in .env to the internal registry path printed after the build
make deploy

# Remove deployment from cluster
make undeploy

# (Optional)Preview rendered manifests before deploying
make dry-run
```

See [OpenShift Deployment](../../../docs/openshift-deployment.md) for details.

### Testing on OpenShift

The route URL is printed after `make deploy`. You can also retrieve it manually:

```bash
oc get route openai-responses-agent -o jsonpath='{.spec.host}'
```

Replace `http://localhost:8000` with `https://<YOUR_ROUTE_URL>` in the API examples below.

## API Endpoints

### POST /chat/completions

Non-streaming:

```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "How much does a Lenovo Laptop cost and what are the reviews?"}], "stream": false}'
```

Streaming:

```bash
curl -sN -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "How much does a Lenovo Laptop cost and what are the reviews?"}], "stream": true}'
```

Pretty Printed Stream:

```bash
curl -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "How much does a Lenovo Laptop cost and what are the reviews?"}], "stream": true}' |
   jq -R -r -j --stream 'scan("^data:(.*)")[] | fromjson.choices[0].delta.content // empty'
```

### GET /health

```bash
curl http://localhost:8000/health
```

## Playground UI

A browser-based chat interface is served directly by the agent at the root URL — no separate process needed.

### Running the Playground

```bash
make run
```

Open [http://localhost:8000](http://localhost:8000) in your browser. A green dot in the header means the agent is connected and ready.

When deployed to OpenShift, the playground is available at the route URL printed by `make deploy`.

### Interactive CLI Chat

For terminal-based testing without a browser:

```bash
make run-cli
```

This launches an interactive prompt where you can pick predefined questions or type your own. Tool calls and results are displayed inline with colored output.

### Standalone Flask Playground (alternative)

You can also run the playground as a separate Flask app that proxies to the agent:

```bash
# Terminal 1: Start the agent
make run

# Terminal 2: Open in the same directory as Terminal 1
uv pip install flask
uv run flask --app playground.app run --port 5050
```

| Variable    | Default                  | Description                     |
|-------------|--------------------------|---------------------------------|
| `AGENT_URL` | `http://localhost:8000`  | URL of the running agent API    |

If the agent runs on a different host or port:

```bash
AGENT_URL=https://your-agent-url uv run flask --app playground.app run --port 5050
```

## Tests

```bash
make test
```

## Resources

- [OpenAI Python Client](https://github.com/openai/openai-python)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create)
