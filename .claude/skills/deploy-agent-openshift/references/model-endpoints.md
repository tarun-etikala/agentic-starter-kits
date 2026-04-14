# Model Endpoint Configuration Reference

Read this file when the user reaches Phase 4 and selects a model endpoint option. Use the relevant section to guide configuration.

## Table of Contents

1. [LlamaStack (discovered)](#llamastack-discovered)
2. [LlamaStack (manual)](#llamastack-manual)
3. [RHOAI / vLLM (discovered)](#rhoai--vllm-discovered)
4. [RHOAI / vLLM (manual)](#rhoai--vllm-manual)
5. [External OpenAI-compatible APIs](#external-openai-compatible-apis)
6. [Manual entry](#manual-entry)

---

## LlamaStack (discovered)

When a LlamaStack service was auto-discovered on the cluster:

| Variable | Value | Notes |
|----------|-------|-------|
| `BASE_URL` | Pre-filled from discovery, e.g., `http://llama-stack.ai-models.svc:8321/v1` | Cluster-internal URL, no connectivity check possible from local machine |
| `MODEL_ID` | Suggest `ollama/llama3.1:8b` (repo default), ask user to confirm | Other common values: `ollama/llama3.2:3b`, `meta-llama/Llama-3.1-8B-Instruct` |
| `API_KEY` | Set to `not-needed` | LlamaStack typically doesn't require authentication |

## LlamaStack (manual)

When user selects LlamaStack but none was auto-discovered:

Ask: "What namespace is LlamaStack running in?"

Construct: `http://llama-stack.<namespace>.svc:8321/v1`

If user doesn't know the namespace, suggest checking:
```bash
oc get svc -A | grep -i llama
```

| Variable | Value |
|----------|-------|
| `BASE_URL` | `http://llama-stack.<namespace>.svc:8321/v1` |
| `MODEL_ID` | Ask user — suggest `ollama/llama3.1:8b` |
| `API_KEY` | `not-needed` |

## RHOAI / vLLM (discovered)

When an InferenceService or model-serving route was auto-discovered:

| Variable | Value | Notes |
|----------|-------|-------|
| `BASE_URL` | Pre-filled from discovery URL + `/v1` suffix | Ensure URL ends with `/v1` |
| `MODEL_ID` | Ask user — depends on deployed model | Check the InferenceService name for hints |
| `API_KEY` | Ask user | May be required depending on serving config |

## RHOAI / vLLM (manual)

Help the user find their model endpoint:

```bash
# Check for InferenceServices
oc get inferenceservice -A 2>/dev/null

# Check for ServingRuntimes
oc get servingruntime -A 2>/dev/null

# Check routes for model-related services
oc get routes -A | grep -iE 'model|llm|vllm|inference|serving'
```

| Variable | Value |
|----------|-------|
| `BASE_URL` | `https://<route-host>/v1` — get from route output |
| `MODEL_ID` | Ask user |
| `API_KEY` | Ask user |

## External OpenAI-compatible APIs

Present sub-options:

| Provider | BASE_URL | Common MODEL_IDs |
|----------|----------|-------------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` |
| Azure OpenAI | `https://<resource>.openai.azure.com/openai/deployments/<deployment>` | Deployment-specific |
| Together AI | `https://api.together.xyz/v1` | `meta-llama/Llama-3.1-8B-Instruct`, `mistralai/Mixtral-8x7B-Instruct-v0.1` |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant`, `mixtral-8x7b-32768` |
| Other | Ask user for URL | Ask user |

For all external providers:
- `API_KEY`: required — ask user to provide
- Validate URL connectivity with a quick test:
  ```bash
  curl -s --max-time 5 -H "Authorization: Bearer ${API_KEY}" "${BASE_URL}/models" | head -c 200
  ```

## Manual entry

Prompt for each value individually:

1. `BASE_URL` — "Enter the model endpoint URL (must end with /v1):"
2. `MODEL_ID` — "Enter the model identifier:"
3. `API_KEY` — "Enter the API key (or 'not-needed' if none required):"

Validate `BASE_URL` ends with `/v1`. If it doesn't, ask: "Your URL doesn't end with /v1. Most OpenAI-compatible APIs expect this. Add /v1? (yes/no)"

---

## Querying available models

After setting `BASE_URL`, always query the `/models` endpoint to discover available models. This works for all OpenAI-compatible APIs:

```bash
curl -s --max-time 10 \
  ${API_KEY:+-H "Authorization: Bearer ${API_KEY}"} \
  "${BASE_URL}/models" | python3 -c "
import json,sys
try:
    data=json.load(sys.stdin)
    models=data.get('data',[])
    if models:
        print('Available models:')
        for i,m in enumerate(models):
            print(f'  ({i+1}) {m[\"id\"]}')
    else:
        print('No models found.')
except Exception as e:
    print(f'Could not list models: {e}')
"
```

**Provider notes:**
- **LlamaStack**: Returns models registered with the stack (e.g., `ollama/llama3.1:8b`). Model IDs include the provider prefix.
- **RHOAI/vLLM**: Returns the deployed model name. Usually one model per endpoint.
- **OpenAI**: Returns all available models. Filter by user's plan.
- **Groq/Together**: Returns all supported models. List can be long — present the most relevant.

If the query fails (connection error, auth required, non-standard API): fall back to asking the user for MODEL_ID manually with the suggested defaults from the provider table above.

---

## Writing values to .env

After collecting all model configuration values, update `.env`:

```bash
# Use sed to replace values in .env
sed -i'' -e "s|^API_KEY=.*|API_KEY=${API_KEY}|" \
         -e "s|^BASE_URL=.*|BASE_URL=${BASE_URL}|" \
         -e "s|^MODEL_ID=.*|MODEL_ID=${MODEL_ID}|" .env
```

If `CONTAINER_IMAGE` is not set, leave it — Phase 5 will handle it based on the build strategy.
