<div style="text-align: center;">

![LangGraph Logo](/images/langgraph_logo.svg)

# Agentic RAG Agent

</div>

---

## What this agent does

RAG agent that indexes documents in a vector store (Milvus) and retrieves relevant chunks to augment the LLM's answers
with your own data.

---

## Quick Start

```bash
cd agents/langgraph/agentic_rag
make init        # creates .env from .env.example
vi .env          # fill in required vars (see below)
make run         # starts on http://localhost:8080
```

## Configuration

### Local

```
API_KEY=not-needed
BASE_URL=http://localhost:8321/v1
MODEL_ID=ollama/llama3.2:3b
EMBEDDING_MODEL=ollama/embeddinggemma:latest
VECTOR_STORE_ID=your-vector-store-id
VECTOR_STORE_PATH=/path/to/milvus_data/milvus_lite.db
```

See [Local Development](../../../docs/local-development.md) for Ollama + Llama Stack setup.

### OpenShift / Remote API

```
API_KEY=your-api-key-here
BASE_URL=https://your-model-endpoint.com/v1
MODEL_ID=llama-3.1-8b-instruct
EMBEDDING_MODEL=your-embedding-model
VECTOR_STORE_ID=your-vector-store-id
CONTAINER_IMAGE=quay.io/your-username/langgraph-agentic-rag:latest
```

## Loading Documents

Before running the agent, load documents into the vector store:

```bash
python data/load_documents.py
```

This will:

- Read documents from `data/sample_knowledge.txt` (or the path in `DOCS_TO_LOAD`)
- Split documents into chunks
- Generate embeddings using `EMBEDDING_MODEL`
- Store chunks in the Milvus vector database

## Running Locally

```bash
uv pip install -e ".[dev]"
make run
```

For local usage, you also need to pull the embedding model:

```bash
ollama pull embeddinggemma:latest
```

## Deploying to OpenShift

```bash
make build       # builds and pushes container image
make deploy      # deploys via Helm (includes volume mount for vector store)
```

See [OpenShift Deployment](../../../docs/openshift-deployment.md) for details.

## API Endpoints

### POST /chat/completions

Non-streaming:

```bash
curl -X POST http://localhost:8080/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is LangChain?"}], "stream": false}'
```

Streaming:

```bash
curl -sN -X POST http://localhost:8080/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is LangChain?"}], "stream": true}'
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

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Milvus Documentation](https://milvus.io/docs)
- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
