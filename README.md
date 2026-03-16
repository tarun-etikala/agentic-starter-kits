<div style="text-align: center;">

![Agentic Starter Kits](/images/ask_logo.png)
# Agentic Starter Kits

</div>

## Purpose
Production-ready agent templates to build and deploy LLM-powered agents on Red Hat OpenShift. Run locally (e.g. with Ollama/Llama Stack) or deploy to any Kubernetes cluster. Each agent has step-by-step docs.

## Agents

Agents are organized by framework. Pick one and follow its README:

| Framework | Agent | Description |
|-----------|-------|-------------|
| **LangGraph** | [ReAct Agent](./agents/langgraph/react_agent/) | General-purpose agent using a ReAct loop: it reasons and calls tools (e.g. search, math) step by step. Built with LangGraph and LangChain. |
| **LangGraph** | [Agentic RAG](./agents/langgraph/agentic_rag/) | RAG agent that indexes documents in a vector store (Milvus) and retrieves relevant chunks to augment the LLM's answers with your own data. |
| **LangGraph** | [ReAct + DB Memory](./agents/langgraph/react_with_database_memory/) | ReAct agent with PostgreSQL-backed conversation memory. Full chat history is persisted in the database while a FIFO sliding window keeps only the last N messages in the LLM context. |
| **LlamaIndex** | [WebSearch Agent](./agents/llamaindex/websearch_agent/) | Agent built on LlamaIndex that uses a web search tool to query the internet and use the results in its answers. |
| **CrewAI** | [WebSearch Agent](./agents/crewai/websearch_agent/) | CrewAI-based agent with a web search tool to query the internet and answer user questions. |
| **Vanilla Python** | [OpenAI Responses Agent](./agents/vanilla_python/openai_responses_agent/) | Minimal agent with no framework: only the OpenAI Python client and an Action/Observation loop with tools. Use with OpenAI or any compatible API. |

## Quick Start

```bash
git clone https://github.com/red-hat-data-services/agentic-starter-kits
cd agentic-starter-kits

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Pick an agent and go
cd agents/langgraph/react_agent
make init        # creates .env from .env.example
vi .env          # fill in API_KEY, BASE_URL, MODEL_ID
make run         # starts on http://localhost:8080
```

## Deployment

Every agent can be deployed to OpenShift (or any Kubernetes cluster) using the shared Helm chart:

```bash
cd agents/langgraph/react_agent
make build       # builds and pushes container image
make deploy      # deploys via Helm
```

See [OpenShift Deployment Guide](./docs/openshift-deployment.md) for details.

## Repository Structure

```
agentic-starter-kits/
├── agents/
│   ├── langgraph/
│   │   ├── react_agent/              # LangGraph ReAct agent
│   │   ├── agentic_rag/             # LangGraph RAG agent with Milvus
│   │   └── react_with_database_memory/ # LangGraph ReAct + PostgreSQL memory
│   ├── crewai/
│   │   └── websearch_agent/         # CrewAI web search agent
│   ├── llamaindex/
│   │   └── websearch_agent/         # LlamaIndex web search agent
│   └── vanilla_python/
│       └── openai_responses_agent/  # OpenAI Responses API (no framework)
├── charts/
│   └── agent/                       # Shared Helm chart for all agents
├── docs/                            # Guides: deployment, local dev, contributing
├── infrastructure/
│   └── llama-stack/                 # Llama Stack server configuration
└── README.md
```

Each agent directory contains:

```
agent-name/
├── agent.yaml         # Agent metadata and required env vars
├── values.yaml        # Helm values override for this agent
├── .env.example       # Environment variable template
├── Makefile           # make init, run, build, deploy, test
├── Dockerfile         # Container build
├── pyproject.toml     # Python dependencies
├── main.py            # FastAPI app (/chat/completions, /health)
├── src/               # Agent source code
├── tests/             # Tests
└── examples/          # Example scripts
```

## Documentation

- [Local Development](./docs/local-development.md) — Ollama + Llama Stack setup
- [OpenShift Deployment](./docs/openshift-deployment.md) — Helm-based deployment guide
- [Adding a New Agent](./docs/adding-a-new-agent.md) — How to contribute a new agent template

## Additional Resources

- **Llama Stack**: https://llama-stack.readthedocs.io/
- **Ollama**: https://docs.ollama.com/
- **Red Hat OpenShift**: https://docs.openshift.com/
- **Helm**: https://helm.sh/docs/
- **Kubernetes**: https://kubernetes.io/docs/

## Contributing

Contributions are welcome! See [Adding a New Agent](./docs/adding-a-new-agent.md) and [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT License
