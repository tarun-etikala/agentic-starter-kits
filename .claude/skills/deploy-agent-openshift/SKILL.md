---
name: deploy-agent-openshift
description: "Interactive deployment guide for agentic-starter-kits agents to Red Hat OpenShift. Use when the user wants to deploy an agent to OpenShift, says 'deploy to openshift', 'deploy agent', 'deploy this agent', asks about OpenShift deployment, or wants to get an agent running on a cluster. Also use when the user is in an agent directory and mentions deployment, clusters, or production. Covers prerequisites, agent selection, cluster login, model endpoint configuration, container build, Helm deploy, and post-deployment verification. Works with any standard agent in the repo."
---

# Deploy Agent to OpenShift

An interactive guide that walks you through deploying any standard agent from this repo to Red Hat OpenShift. Follow the phases in order — each phase has a checkpoint that detects existing state so you can skip completed work.

This repo is a quickstart for showcasing OpenShift's agentic AI capabilities. Always use the repo's `make` commands rather than running raw `oc apply`, `helm install`, or `kubectl` directly — the Makefiles encapsulate the correct flags, secrets handling, and conventions.

## How to interact

- Use `AskUserQuestion` to present choices and collect input from the user
- Use `Bash` to run `make`, `oc`, and `helm` commands
- Use `Read` to parse `agent.yaml` and `.env` files
- Present numbered menus for selections — prefer multiple choice over open-ended questions
- On failure at any phase: diagnose the error, suggest a fix, ask the user if they want to retry that phase. Do not re-run earlier phases.

## Phase 1: Prerequisites Check

Check that all required CLI tools are installed. Run these checks in parallel using Bash:

```bash
command -v oc && oc version --client 2>/dev/null
command -v helm && helm version --short 2>/dev/null
command -v make && make --version 2>/dev/null | head -1
command -v podman 2>/dev/null && echo "podman: available" || echo "podman: not found"
command -v docker 2>/dev/null && echo "docker: available" || echo "docker: not found"
```

**Blocking tools** (stop if missing): `oc`, `helm`, `make`
- If `oc` is missing: "Install the OpenShift CLI: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html"
- If `helm` is missing: "Install Helm 3: https://helm.sh/docs/intro/install/"
- If `make` is missing: "Install GNU Make (usually included with Xcode CLI tools on macOS: `xcode-select --install`)"

**Non-blocking tools**: `podman`, `docker`
- If neither is found: inform the user that in-cluster build (`make build-openshift`) will be used in Phase 5. This is not a blocker.
- Note which container CLI is available — store this for Phase 5.

Present a summary of prerequisites and proceed only if all blocking tools are installed.

## Phase 2: Agent Selection

**Checkpoint:** Check if the current working directory contains an `agent.yaml` file.

```bash
test -f agent.yaml && cat agent.yaml
```

- If `agent.yaml` exists: parse it, show the agent's `displayName` and `description`, ask: "Deploy this agent (<displayName>)? (yes / choose a different agent)"
- If the user confirms: note the current directory as the agent directory and proceed to Phase 3
- If no `agent.yaml` or user wants to choose: proceed to discovery below

**Discovery:**

Find the repo root (look for the `agents/` directory by walking up from cwd or checking common locations):

```bash
# From repo root
find agents/ -name "agent.yaml" -type f | sort
```

For each `agent.yaml` found, parse `name`, `displayName`, `framework`, `description`, and check for `deploymentModel`.

**Filter out non-standard agents:**
- Any agent with `deploymentModel: flow-import` (e.g., langflow) — explain: "Uses Podman Compose flow-import, not standalone container deployment"
- Any agent under `agents/a2a/` — explain: "Uses a different chart, base image, and entrypoint"

Present a numbered menu of standard agents:

```
Available agents for deployment:

  (1) LangGraph ReAct Agent — General-purpose ReAct agent with reason-and-act loop
  (2) LangGraph Agentic RAG — RAG agent with document retrieval
  (3) CrewAI Websearch Agent — Multi-agent websearch with CrewAI
  ...

Excluded (non-standard deployment):
  - Langflow Simple Tool Calling Agent (flow-import model)
  - A2A LangGraph CrewAI Agent (multi-container setup)

Which agent would you like to deploy?
```

After selection, `cd` into the agent directory. All subsequent `make` commands run from this directory.

## Phase 3: OpenShift Login & Project Selection

**Checkpoint:** Check if already logged into OpenShift.

```bash
oc whoami 2>/dev/null && oc whoami --show-server 2>/dev/null
```

- If successful: show "Logged in as `<user>` to `<server>`", ask to continue or re-login
- If fails: guide the user through login

**Login guidance:**

```
You're not logged into OpenShift. You need to run:

  oc login --token=<token> --server=https://<cluster-api-url>

Get your login token from your cluster's OAuth page (usually at
https://<cluster-console>/oauth/token/request).

Let me know when you've logged in.
```

After the user confirms, re-check `oc whoami`. If still failing, ask again.

**Project selection:**

```bash
echo "Current project: $(oc project -q)"
echo "---"
oc projects 2>/dev/null
```

Present options to the user:
1. Use current project (`<current-project>`)
2. Switch to an existing project (show list from `oc projects`)
3. Create a new project

If switching: `oc project <name>`
If creating: ask for project name, then `oc new-project <name>`

Confirm the active project before proceeding:
```bash
oc project -q
```

## Phase 4: Model Endpoint Configuration

**Checkpoint:** Check if `.env` already exists with non-placeholder values.

```bash
test -f .env && cat .env
```

If `.env` exists and has real values (not the defaults from `.env.example` like `not-needed-for-local-development` or empty values) for `API_KEY`, `BASE_URL`, `MODEL_ID`: show them and ask "Use these settings? (yes / reconfigure)"

If no `.env` or user wants to reconfigure: run `make init` to create `.env` from `.env.example`.

**Cluster discovery (best-effort):**

Before presenting the model menu, scan the cluster for existing model services. Run these checks — silently skip any that fail due to permissions:

```bash
# LlamaStack services (port 8321 or name contains "llama")
oc get svc -A -o json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
for svc in data.get('items',[]):
    name=svc['metadata']['name']
    ns=svc['metadata']['namespace']
    ports=[p.get('port') for p in svc['spec'].get('ports',[])]
    if 8321 in ports or 'llama' in name.lower():
        print(f'  LlamaStack: {name}.{ns}.svc:{8321} (namespace: {ns})')
" 2>/dev/null || true

# RHOAI InferenceService endpoints
oc get inferenceservice -A -o custom-columns='NAME:.metadata.name,NAMESPACE:.metadata.namespace,URL:.status.url' --no-headers 2>/dev/null || true

# Routes that look like model endpoints
oc get routes -A -o custom-columns='NAME:.metadata.name,NAMESPACE:.metadata.namespace,HOST:.spec.host' --no-headers 2>/dev/null | grep -iE 'model|llm|vllm|llama|inference|serving' || true
```

**Present adaptive menu:**

If cluster services were discovered, show them as numbered options with pre-filled URLs at the top. Always include manual/external options below.

If no cluster services found:
```
No model endpoints auto-detected on the cluster.

  (1) LlamaStack (enter namespace to construct URL)
  (2) RHOAI / vLLM model serving (enter route URL)
  (3) External OpenAI-compatible API (OpenAI, Azure, Groq, Together, etc.)
  (4) Enter all values manually
```

For detailed URL patterns and provider-specific guidance, read `references/model-endpoints.md` in this skill directory.

**After model config — handle extra env vars:**

Read `agent.yaml` to check for required env vars beyond `API_KEY`, `BASE_URL`, `MODEL_ID`:

```bash
cat agent.yaml
```

Parse `env.required` list. For each required var that isn't `API_KEY`, `BASE_URL`, or `MODEL_ID`, check if it's set in `.env`. If not, read `.env.example` for context/comments about what the var does, and prompt the user for a value.

Common extra vars by agent:
- `react_with_database_memory`: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `agentic_rag`: `EMBEDDING_MODEL`, `VECTOR_STORE_*` (these are optional but useful to mention)

**Model discovery — query available models:**

After `BASE_URL` is set (and `API_KEY` if needed), query the endpoint to list available models. This lets the user pick from real models instead of guessing `MODEL_ID`.

```bash
# Query available models from the endpoint
curl -s --max-time 10 \
  ${API_KEY:+-H "Authorization: Bearer ${API_KEY}"} \
  "${BASE_URL}/models" | python3 -c "
import json,sys
try:
    data=json.load(sys.stdin)
    models=data.get('data',[])
    if models:
        print('Available models on this endpoint:')
        for i,m in enumerate(models):
            print(f'  ({i+1}) {m[\"id\"]}')
    else:
        print('No models found on this endpoint.')
except Exception as e:
    print(f'Could not list models: {e}')
" 2>/dev/null
```

- If models are listed: present them as a numbered menu for the user to pick `MODEL_ID`
- If the query fails or returns empty: ask the user to enter `MODEL_ID` manually
- This works for any OpenAI-compatible endpoint (LlamaStack, vLLM, OpenAI, etc.)

**Validation:**

After all values are set:
1. Verify `BASE_URL` ends with `/v1` — if not, warn and ask to correct
2. Source `.env` and check all required vars are non-empty (mirrors the Makefile's `_check-env` target):
   ```bash
   source .env 2>/dev/null && for var in API_KEY BASE_URL MODEL_ID; do eval val=\$$var; [ -n "$val" ] && echo "$var: set" || echo "$var: MISSING"; done
   ```
3. For cluster-internal URLs (`*.svc:*`): skip connectivity check (model listing above already validates reachable endpoints), note "This is a cluster-internal URL — it will be validated after deployment."

## Phase 5: Build Container Image

**Checkpoint:** Determine the build strategy based on available tools.

Check which container CLI is available (this was noted in Phase 1, but re-check):
```bash
command -v podman 2>/dev/null && echo "podman" || (command -v docker 2>/dev/null && echo "docker" || echo "none")
```

**If podman or docker is available:**

Present choice to the user:
```
You have <podman/docker> available. Two build options:

  (A) Local build + push — build locally, push to a registry (Quay.io, Docker Hub, GHCR)
      Requires: registry account, CONTAINER_IMAGE set in .env
      Commands: make build → make push

  (B) In-cluster build — build inside OpenShift, no local container tools needed
      Requires: just oc CLI (already verified)
      Commands: make build-openshift

Option B is simpler if you don't have a registry set up. Which do you prefer?
```

**If neither podman nor docker is available:**

Inform user: "No local container CLI found. Using in-cluster build (make build-openshift) — this only needs the oc CLI."

Auto-select in-cluster build.

### Build Path A: Local build + push

**Check for existing image (checkpoint):**
```bash
source .env && ${CONTAINER_CLI:-podman} images 2>/dev/null | grep "${CONTAINER_IMAGE%:*}" || echo "No existing image found"
```
If found, ask: "Image already exists locally. Rebuild or skip to push?"

**Step A1: Ensure CONTAINER_IMAGE is set**

```bash
source .env && echo "CONTAINER_IMAGE=${CONTAINER_IMAGE}"
```

If empty or not set, ask the user:
```
CONTAINER_IMAGE needs to be set — this is where the image will be pushed.

Format: <registry>/<namespace>/<image-name>:<tag>

Examples:
  quay.io/your-username/langgraph-react-agent:latest
  docker.io/your-username/langgraph-react-agent:latest
  ghcr.io/your-org/langgraph-react-agent:latest

Enter your CONTAINER_IMAGE:
```

Update `.env` with the value:
```bash
sed -i'' -e "s|^#*CONTAINER_IMAGE=.*|CONTAINER_IMAGE=${VALUE}|" .env
```

**Step A2: Verify registry login**

Ask: "Are you logged into your container registry? If not, run: `podman login <registry>` (or `docker login <registry>`)"

Wait for user confirmation.

**Step A3: Build**

Inform the user: "Building the container image locally. This may take 1-2 minutes depending on your machine."

```bash
make build
```

On failure, read the error output. Common causes:
- "neither podman nor docker found" → container CLI issue
- Dockerfile syntax errors → show the specific error line
- Disk space → suggest `podman system prune` or `docker system prune`

Ask "Want to retry?" on failure.

**Step A4: Push**
```bash
make push
```

On failure:
- "unauthorized" or "access denied" → "Not logged into registry. Run: `podman login <registry>`"
- "not found" or "repository does not exist" → "Check CONTAINER_IMAGE format — the namespace/repo may need to be created first"

Ask "Want to retry?" on failure.

### Build Path B: In-cluster build

**Check for existing BuildConfig (checkpoint):**
```bash
AGENT_NAME=$(python3 -c "import re; print(re.search(r'^name:\s*(.+)', open('agent.yaml').read(), re.M).group(1).strip())")
oc get bc/${AGENT_NAME} 2>/dev/null && echo "BuildConfig exists" || echo "No existing BuildConfig"
```
If BuildConfig exists, ask: "BuildConfig already exists. Rebuild or use existing image?"

**Step B1: Build in cluster**

Before running, inform the user: "Building the container image in-cluster. This typically takes 1-2 minutes — you'll see the build logs streaming below."

```bash
make build-openshift
```

This command streams build logs via `oc start-build --follow` and outputs the internal registry URL after success. Capture it.

On failure:
- "forbidden" → "Insufficient permissions on this namespace. Check with your cluster admin."
- Build errors → show `oc logs bc/<agent-name>` output

**Step B2: Update CONTAINER_IMAGE in .env**

After successful build, get the namespace and update `.env`:
```bash
NS=$(oc project -q)
AGENT_NAME=$(python3 -c "import re; print(re.search(r'^name:\s*(.+)', open('agent.yaml').read(), re.M).group(1).strip())")
INTERNAL_IMAGE="image-registry.openshift-image-registry.svc:5000/${NS}/${AGENT_NAME}:latest"
sed -i'' -e "s|^#*CONTAINER_IMAGE=.*|CONTAINER_IMAGE=${INTERNAL_IMAGE}|" .env
echo "Set CONTAINER_IMAGE=${INTERNAL_IMAGE}"
```

## Phase 6: Deploy

**Checkpoint:** Check if a Helm release already exists for this agent.

```bash
AGENT_NAME=$(python3 -c "import re; print(re.search(r'^name:\s*(.+)', open('agent.yaml').read(), re.M).group(1).strip())")
helm list -q 2>/dev/null | grep "^${AGENT_NAME}$" && echo "EXISTING RELEASE FOUND" || echo "No existing release"
```

If an existing release is found:
- Inform user: "Existing deployment of `<agent-name>` found. Removing it for a clean deploy."
- Run: `make undeploy`
- Wait for confirmation, then proceed with fresh deploy

**Step 1: Preview manifests**

```bash
make dry-run
```

Show the output (secrets are automatically redacted by the Makefile). Ask user: "Here are the Kubernetes resources that will be created. Proceed with deployment? (yes/no)"

**Step 2: Deploy**

Inform the user: "Deploying to OpenShift. This typically takes 30-60 seconds — Helm will install the chart and wait for the pod to become ready."

```bash
make deploy
```

The Makefile runs `helm upgrade --install`, waits for rollout (`oc rollout status --timeout=120s`), and prints the route URL.

**On failure — diagnose:**

If the deploy command itself fails (Helm error):
- Show the full error output
- Common cause: missing env vars → suggest re-running Phase 4

If rollout times out or pods aren't ready, diagnose:
```bash
AGENT_NAME=$(python3 -c "import re; print(re.search(r'^name:\s*(.+)', open('agent.yaml').read(), re.M).group(1).strip())")
echo "=== Pod Status ==="
oc get pods -l app.kubernetes.io/name=${AGENT_NAME}
echo "=== Pod Events ==="
oc describe pod -l app.kubernetes.io/name=${AGENT_NAME} | tail -30
echo "=== Pod Logs ==="
oc logs deployment/${AGENT_NAME} --tail=50 2>/dev/null
```

Common failure patterns:
- **ImagePullBackOff**: "OpenShift can't pull the container image. Either make the image public, or configure an image pull secret. See: https://docs.openshift.com/container-platform/latest/openshift_images/managing_images/using-image-pull-secrets.html"
- **CrashLoopBackOff**: "Pod is crashing. Likely cause: misconfigured env vars (API_KEY, BASE_URL, MODEL_ID). Check the logs above."
- **Pending (Insufficient resources)**: "Cluster doesn't have enough resources. Try reducing requests in values.yaml."
- **ErrImagePull**: "Image tag or repository not found. Verify CONTAINER_IMAGE in .env matches the pushed image."

Ask: "Want to retry the deployment? (I'll run `make undeploy` first, then `make deploy`)"

If yes: run `make undeploy`, then `make deploy`.

## Phase 7: Verify & Showcase

This phase always runs fresh — no checkpoint. It validates the deployment end-to-end and presents the user with ready-to-use commands.

**Step 1: Get the route URL**

```bash
AGENT_NAME=$(python3 -c "import re; print(re.search(r'^name:\s*(.+)', open('agent.yaml').read(), re.M).group(1).strip())")
ROUTE_URL=$(oc get route ${AGENT_NAME} -o jsonpath='{.spec.host}' 2>/dev/null)
echo "Route: https://${ROUTE_URL}"
```

If no route found, check: `oc get routes` — the route may have a different name.

**Step 2: Health check (with retry)**

The pod may take up to a minute to become ready. Retry the health check up to 3 times with 15-second intervals:

```bash
for i in 1 2 3; do
  echo "Health check attempt ${i}/3..."
  STATUS=$(curl -s --max-time 10 -o /tmp/health_response -w "%{http_code}" "https://${ROUTE_URL}/health" 2>/dev/null)
  if [ "$STATUS" = "200" ]; then
    echo "Health check passed!"
    cat /tmp/health_response
    break
  fi
  if [ "$i" -lt 3 ]; then
    echo "Not ready yet (HTTP ${STATUS}). Waiting 15s..."
    sleep 15
  else
    echo "Health check failed after 3 attempts (HTTP ${STATUS})"
    cat /tmp/health_response 2>/dev/null
  fi
done
```

On health check failure, diagnose:
```bash
echo "=== Pod Status ==="
oc get pods -l app.kubernetes.io/name=${AGENT_NAME}
echo "=== Recent Logs ==="
oc logs deployment/${AGENT_NAME} --tail=30 2>/dev/null
```

Suggest: pod may still be starting, env vars misconfigured, or image issue. Read `references/error-diagnosis.md` for detailed guidance.

**Step 3: Functional test — POST /chat/completions**

```bash
RESPONSE=$(curl -s --max-time 30 -X POST "https://${ROUTE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is 2+2?"}], "stream": false}')
echo "${RESPONSE}" | python3 -c "import json,sys; print(json.dumps(json.loads(sys.stdin.read(),strict=False),indent=2))" 2>/dev/null || echo "${RESPONSE}"
```

Validate the response:
```bash
echo "${RESPONSE}" | python3 -c "
import json,sys
try:
    data=json.loads(sys.stdin.read(),strict=False)
    content=data['choices'][0]['message']['content']
    if content:
        print(f'Agent responded: {content[:200]}')
        print('Functional test PASSED')
    else:
        print('WARNING: Response content is empty')
except (KeyError, IndexError, json.JSONDecodeError) as e:
    print(f'Functional test FAILED: {e}')
    sys.exit(1)
"
```

On `/chat/completions` failure, diagnose by HTTP status:
- **401/403**: "API_KEY is wrong or missing. Update API_KEY in .env and redeploy."
- **500**: "Internal server error. Check pod logs: `oc logs deployment/<agent-name> --tail=50`"
- **Connection refused / timeout**: "Model endpoint unreachable from the pod. BASE_URL may not be accessible from inside the cluster. If using a cluster-internal URL, verify the model service is running."
- **Invalid JSON response**: "Response doesn't match expected format. Check MODEL_ID is correct for your endpoint."

Read `references/error-diagnosis.md` for more detailed diagnosis steps.

**Step 4: Success summary**

If both health check and functional test pass, print:

```
Agent "<displayName>" deployed successfully!

Route: https://<route-url>

Quick commands:

  # Health check
  curl https://<route-url>/health

  # Chat (non-streaming)
  curl -X POST https://<route-url>/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "Hello!"}], "stream": false}'

  # Chat (streaming)
  curl -sN -X POST https://<route-url>/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "Hello!"}], "stream": true}'

Cleanup:
  cd <agent-directory>
  make undeploy
```

Replace all `<route-url>` and `<agent-directory>` with actual values. Get `displayName` from `agent.yaml`.
