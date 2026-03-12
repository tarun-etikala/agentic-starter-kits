<div style="text-align: center;">

![Agentic Starter Kits](/images/ask_logo.png)
# Agentic Starter Kits

</div>

## Purpose

Production-ready agent templates to build and deploy LLM-powered agents. Run locally (e.g. with Ollama/Llama Stack) or
deploy to Red Hat OpenShift. Each agent has step-by-step docs.

## Agents

Agents are organized by framework. Pick one and follow its README:

| Framework | Agent | Description |
|-----------|-------|-------------|
| **LangGraph** | [ReAct Agent](./agents/langgraph/react_agent/) | General-purpose ReAct loop: reasons and calls tools (search, math) step by step |
| **LangGraph** | [Agentic RAG](./agents/langgraph/agentic_rag/) | RAG agent that indexes documents in Milvus and retrieves relevant chunks to augment answers |
| **LangGraph** | [ReAct + DB Memory](./agents/langgraph/react_with_database_memory/) | ReAct agent with PostgreSQL-backed conversation memory for persistent chat history |
| **LlamaIndex** | [WebSearch Agent](./agents/llamaindex/websearch_agent/) | Uses a web search tool to query the internet and augment answers |
| **CrewAI** | [WebSearch Agent](./agents/crewai/websearch_agent/) | ReAct-style crew with a web search tool to answer user questions |
| **OpenAI** | [Responses Agent](./agents/openai/responses_agent/) | Minimal agent with no framework: OpenAI client + Action/Observation loop with tools |

## Deployment Options

Agents in this repository can support two deployment modes:

### 🖥️ Local Development

- Run agents on your local machine
- Use Llama Stack server with Ollama for model serving
- Ideal for development, testing, and experimentation
- No cloud infrastructure required

### ☁️ Production Deployment

- Deploy agents to Red Hat OpenShift Cluster
- Containerized deployment with Kubernetes
- Production-grade scaling and monitoring
- CI/CD ready

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
│   └── openai/
│       └── responses_agent/         # OpenAI Responses API (no framework)
├── infrastructure/
│   └── llama-stack/                 # Llama Stack server configuration
└── README.md
```

---

## How to Use This Repository

1. **Start Here**: Read this README to understand the overall structure and install core dependencies
2. **Choose an Agent**: Select an agent from the `agents/` directory based on your use case
3. **Follow Agent README**: Navigate to the agent's directory and follow its specific README for:
    - Agent-specific dependencies installation
    - Configuration and setup
    - Local development or OpenShift deployment
    - Usage examples and API endpoints

### Pre-requisitions to run that repo

Run this script to set up repo stuff with a use of [UV](https://docs.astral.sh/uv/) and python 3.12

Download repo

```bash
git clone https://github.com/red-hat-data-services/agentic-starter-kits
```

Get into root dir

```bash
cd agentic-starter-kits
```

Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Additional Resources

- **Llama Stack Documentation**: https://llama-stack.readthedocs.io/
- **Ollama Documentation**: https://docs.ollama.com/
- **OpenShift Documentation**: https://docs.openshift.com/
- **Kubernetes**: https://kubernetes.io/docs/

## Contributing

Contributions are welcome! Please see individual agent READMEs for specific guidelines.

## License

MIT License

Copyright (c) 2026
