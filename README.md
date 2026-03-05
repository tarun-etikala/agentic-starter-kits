<div style="text-align: center;">

![Agentic Starter Kits](/images/ask_logo.png)
# Agentic Starter Kits

</div>

## Purpose
Production-ready agent templates to build and deploy LLM-powered agents. Run locally (e.g. with Ollama/Llama Stack) or deploy to Red Hat OpenShift. Each agent has step-by-step docs.

## Agents
Choose an agent and follow its README for setup and deployment:

- **[LangGraph ReAct](./agents/langgraph/react_agent/README.md)** – General-purpose agent using a ReAct loop: it reasons and calls tools (e.g. search, math) step by step. Built with LangGraph and LangChain.
- **[LlamaIndex WebSearch](./agents/llamaindex/websearch_agent/README.md)** – Agent built on LlamaIndex that uses a web search tool to query the internet and use the results in its answers.
- **[OpenAI Responses](./agents/openai/responses_agent/README.md)** – Minimal agent with no framework: only the OpenAI Python client and an Action/Observation loop with tools. Use with OpenAI or any compatible API.
- **[LangGraph Agentic RAG](./agents/langgraph/agentic_rag/README.md)** – RAG agent that indexes documents in a vector store (Milvus) and retrieves relevant chunks to augment the LLM’s answers with your own data.

## Deployment Options
Agents in this repository can support two deployment modes:

### 🖥️ Local Development
- Run agents on your local machine
- Use Llama Stack server with Ollama for model serving
- Ideal for development, testing, and experimentation
- No cloud infrastructure required

### ☁️ Production Deployment
- Deploy agents to Red Hat OpenShift Cluster using `agentctl` + Helm charts
- Single-command deployment: `./scripts/agentctl deploy <image> --namespace <ns>`
- Production-grade scaling and monitoring
- CI/CD and GitOps ready (ArgoCD / OpenShift GitOps)

## Repository Structure

```
agentic-starter-kits/
├── .env.example                        # Environment config template
├── scripts/
│   └── agentctl                        # CLI for deploy, destroy, list, status
├── charts/
│   └── agent/                          # Helm chart for all agents
├── agents/
│   ├── langgraph/
│   │   ├── react_agent/                # LangGraph ReAct agent
│   │   └── agentic_rag/                # RAG agent with Milvus vector store
│   ├── llamaindex/
│   │   └── websearch_agent/            # LlamaIndex web search agent
│   └── openai/
│       └── responses_agent/            # OpenAI Responses API (no framework)
├── run_llama_server.yaml               # Llama Stack server configuration
└── README.md
```

---

## How to Use This Repository

### Prerequisites
- [UV](https://docs.astral.sh/uv/) package manager
- Python 3.12
- [Helm](https://helm.sh/) (for OpenShift deployment)
- `oc` CLI (for OpenShift deployment)

### Quick Start

```bash
# Clone the repo
git clone https://github.com/red-hat-data-services/agentic-starter-kits
cd agentic-starter-kits

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and model endpoint

# Choose an agent and run locally
cd agents/langgraph/react_agent
cp template.env .env
# Edit .env with your values
uv pip install .
uvicorn main:app --host 0.0.0.0 --port 8080
```

### Deploy to OpenShift

```bash
# Build and push the agent image
docker build -t quay.io/team/react-agent:v1 agents/langgraph/react_agent/
docker push quay.io/team/react-agent:v1

# Deploy with agentctl
./scripts/agentctl deploy quay.io/team/react-agent:v1 \
  --namespace dev-sandbox \
  --agent langgraph/react_agent

# Check status
./scripts/agentctl status react-agent -n dev-sandbox

# List all deployed agents
./scripts/agentctl list

# Tear down
./scripts/agentctl destroy react-agent -n dev-sandbox
```

---

## Additional Resources
- **Llama Stack Documentation**: https://llama-stack.readthedocs.io/
- **Ollama Documentation**: https://docs.ollama.com/
- **OpenShift Documentation**: https://docs.openshift.com/
- **Kubernetes**: https://kubernetes.io/docs/
- **Helm Documentation**: https://helm.sh/docs/

## Contributing
Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new agents, deploy with agentctl, and follow commit conventions.

## License
MIT License