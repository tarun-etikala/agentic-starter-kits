# Post-Helm Migration Audit

**Date:** 2026-04-08 (updated 2026-04-16, PR #63 resolved)
**Scope:** All 11 agents, 2 Helm charts, Dockerfiles, main.py entry points, values.yaml overrides, and deployment docs

---

## Overview

The repo has migrated to a shared Helm chart (`charts/agent/`) for deploying agents to OpenShift/Kubernetes. A dedicated chart (`charts/a2a-langgraph-crewai/`) handles multi-agent A2A orchestration. This audit covers issues, inconsistencies, and improvements identified after the migration.

---

## Resolved Issues (as of 2026-04-16)

The following issues have been fixed since the initial audit. They are kept here for traceability and marked ~~strikethrough~~ in their original sections below.

| # | Issue | Fixed In |
|---|-------|----------|
| ~~1~~ | Root README missing 3 agents (table) | PR #63 (`fix: update root README, and harden Helm chart`) — human_in_the_loop, google/adk, a2a added to agents table |
| ~~4~~ | Raw K8s manifests bypass Helm | PR #56 (`feat: automl mcp migration`) — `k8s/` directory removed, deployment migrated to shared Helm chart |
| ~~10~~ | No generic secrets mechanism in shared Helm chart | PR #56 — `extraSecrets` map added to `charts/agent/templates/secret.yaml` and `values.yaml` |
| ~~28~~ | `mcp_automl_template` Dockerfile uses GID `appuser` | PR #56 — rebuilt with UBI9 base, pinned uv, `chown 1001:0`, proper `HOME`/`PYTHONPATH` |
| ~~31~~ | Empty `image.repository` renders invalid image references | PR #63 — added `{{ required }}` validation on `image.repository` in shared Helm chart |
| ~~38~~ | `.PHONY` mismatch in Google ADK Makefile | PR #63 — corrected `llama` → `llama-server` in `.PHONY` declaration |
| ~~47~~ | CONTRIBUTING.md commit scope format inconsistency | PR #57 — scope format clarified with explicit examples |
| ~~48~~ | Root README directory tree missing agents and charts | PR #63 — added `google/`, `a2a/`, `human_in_the_loop/`, `charts/a2a-langgraph-crewai/` to tree |
| ~~51~~ | `make deploy` does not handle stale secrets on redeployment | PR #63 — added `checksum/secret` annotation to `charts/agent/templates/deployment.yaml` pod template |
| ~~5~~ | Health check returns HTTP 200 when agent uninitialized | This branch — all 8 agents now return HTTP 503 with `JSONResponse` when not initialized, matching AutoGen pattern |
| ~~24~~ | `POSTGRES_PASSWORD` missing from `react_with_database_memory/values.yaml` | Not an issue — correctly handled via `secrets.postgresPassword` in shared chart |
| ~~33~~ | FastAPI version fragmentation | This branch — standardized all agents to `>=0.135.1` |
| ~~34~~ | Uvicorn version mismatch in `mcp_automl_template` | This branch — bumped `uvicorn[standard]>=0.30.0` to `>=0.41.0` |
| ~~36~~ | Makefile `run-app` binds to `0.0.0.0` (DNS rebinding risk) | This branch — all 9 agents now bind to `127.0.0.1` for local dev |
| ~~46~~ | `env: init` dependency inconsistency | This branch — removed `init` dependency from `env` target in `react_with_database_memory/Makefile` |

**Issues #6 and #7 are partially fixed:** `mcp_automl_template/Dockerfile` now uses UBI9 + pinned uv, but `a2a/langgraph_crewai_agent/Dockerfile` still uses `python:3.12-slim` + `uv:latest`.

---

## Agents Inventory

| # | Framework | Agent | Helm Chart | Notes |
|---|-----------|-------|------------|-------|
| 1 | LangGraph | react_agent | `charts/agent` | Standard |
| 2 | LangGraph | agentic_rag | `charts/agent` | Volumes for vector store |
| 3 | LangGraph | react_with_database_memory | `charts/agent` | PostgreSQL support |
| 4 | LangGraph | human_in_the_loop | `charts/agent` | Standard |
| 5 | LlamaIndex | websearch_agent | `charts/agent` | Standard |
| 6 | CrewAI | websearch_agent | `charts/agent` | Standard |
| 7 | Vanilla Python | openai_responses_agent | `charts/agent` | Standard |
| 8 | AutoGen | mcp_agent | `charts/agent` | MCP tools over SSE |
| 9 | Google ADK | adk | `charts/agent` | Standard |
| 10 | A2A | langgraph_crewai_agent | `charts/a2a-langgraph-crewai` | Two-phase deployment |
| 11 | Langflow | simple_tool_calling_agent | None | Flow-import model, local-only |

---

## Issues Found

### High Priority

#### ~~1. Root README Missing 3 Agents~~ ✅ RESOLVED

**Resolved in:** PR #63 (`fix: update root README, and harden Helm chart`). All 3 agents added to the README table and directory tree.

#### 2. PORT Default Mismatch (8000 vs 8080)

**Files:** All `main.py` files

Every `main.py` defaults to port `8000` when `PORT` is unset:

```python
port = int(getenv("PORT", 8000))
```

But the Dockerfile sets `ENV PORT=8080` and the Helm chart defaults to `service.port: 8080`. The fallback should be `8080` for consistency. This only affects local `python main.py` runs (containers always set `PORT=8080`), but is confusing.

**Affected files:**

- `agents/langgraph/react_agent/main.py`
- `agents/langgraph/agentic_rag/main.py`
- `agents/langgraph/react_with_database_memory/main.py`
- `agents/langgraph/human_in_the_loop/main.py`
- `agents/llamaindex/websearch_agent/main.py`
- `agents/crewai/websearch_agent/main.py`
- `agents/vanilla_python/openai_responses_agent/main.py`
- `agents/autogen/mcp_agent/main.py`
- `agents/google/adk/main.py`

#### 3. A2A Port Default Is 9200, Not 8080

**File:** `agents/a2a/langgraph_crewai_agent/` (Python code)

The A2A agent's code defaults to port `9200` (LangGraph) / `9100` (CrewAI) when `PORT` is unset, conflicting with its Dockerfile's `ENV PORT=8080`.

#### ~~4. Raw K8s Manifests Bypass Helm~~ ✅ RESOLVED

**Resolved in:** PR #56 (`feat: automl mcp migration`). The `k8s/` directory was removed and MCP server deployment migrated to the shared Helm chart with a dedicated `values.yaml` override.

#### ~~5. Health Check HTTP Status Code Inconsistency~~ ✅ RESOLVED

**Resolved in:** This branch. All 8 agents now return HTTP 503 with `JSONResponse` when uninitialized, matching the AutoGen pattern. Import of `JSONResponse` added to each `main.py`.

---

### Medium Priority

#### 6. Dockerfiles Using Wrong Base Image (partially fixed)

**Remaining file:**

- `agents/a2a/langgraph_crewai_agent/Dockerfile` -- still uses `python:3.12-slim`

~~`agents/autogen/mcp_agent/mcp_automl_template/Dockerfile`~~ -- ✅ fixed in PR #56 (now UBI9)

The project convention (documented in `docs/adding-a-new-agent.md`) mandates `registry.access.redhat.com/ubi9/python-312`. Using `python:3.12-slim` risks Docker Hub rate limits on OpenShift and loses UBI9's FIPS/security certifications.

#### 7. Unpinned uv Version in Dockerfile (partially fixed)

**Remaining file:**

- `agents/a2a/langgraph_crewai_agent/Dockerfile` -- still uses `ghcr.io/astral-sh/uv:latest`

~~`agents/autogen/mcp_agent/mcp_automl_template/Dockerfile`~~ -- ✅ fixed in PR #56 (now pinned SHA)

All other Dockerfiles pin uv to a specific SHA digest for reproducible builds:

```dockerfile
COPY --from=ghcr.io/astral-sh/uv@sha256:fc93e9ec... /uv /usr/local/bin/uv
```

#### 8. AutoGen Response Format Breaks OpenAI Compatibility

**File:** `agents/autogen/mcp_agent/main.py`

The `/chat/completions` response model uses `messages` + `tool_invocations` fields instead of the OpenAI-compatible `choices` array used by all other agents. This breaks the stated contract in `docs/adding-a-new-agent.md`:

> All agents must expose: `POST /chat/completions` -- returns JSON response

#### 9. pymilvus Version Fragmentation

**Files:** Various `pyproject.toml`

Three different pinned versions across agents:

- `react_agent` & `agentic_rag`: `pymilvus==2.6.9`
- `human_in_the_loop` & `react_with_database_memory`: `pymilvus==2.5.9` or `2.5.7`
- `google/adk`: `pymilvus>=2.4.10` (unpinned)

Should standardize to one safe version.

#### ~~10. No Generic Secrets Mechanism in Shared Helm Chart~~ ✅ RESOLVED

**Resolved in:** PR #56. An `extraSecrets` map was added to `charts/agent/templates/secret.yaml` and `values.yaml`, allowing arbitrary secret key-value pairs without chart modifications.

#### 11. Langflow Has No OpenShift Deployment Path

**Directory:** `agents/langflow/simple_tool_calling_agent/`

This agent has no Dockerfile, no `values.yaml`, and no Helm integration. It uses `podman-compose` for local development only. While `agent.yaml` correctly sets `deploymentModel: flow-import`, there's no guidance on deploying it to OpenShift.

#### 12. A2A Chart Missing Route Toggle and Ingress Support

**Directory:** `charts/a2a-langgraph-crewai/`

Unlike the shared chart, the A2A chart:

- Has no `openshift.route.enabled` toggle -- Routes are always created
- Has no Ingress support for vanilla Kubernetes

---

### Low Priority

#### 13. Duplicate API Endpoints

**Files:**

- `agents/crewai/websearch_agent/main.py`
- `agents/llamaindex/websearch_agent/main.py`
- `agents/vanilla_python/openai_responses_agent/main.py`

These three agents expose duplicate `/api/chat` and `/api/health` aliases alongside the standard `/chat/completions` and `/health`. Purpose is undocumented.

#### 14. Unused flask Dependency

**Files:** Most `pyproject.toml` files

`flask` is listed as a dependency in most agents but is not imported in any `main.py`. Likely a leftover from earlier development.

#### 15. LOG_LEVEL Not Respected

**Files:** All `main.py` except A2A

Only the A2A agent reads `LOG_LEVEL` from environment. All other agents ignore it, using Python's default log level. This makes production debugging harder.

#### 16. Hardcoded Recursion Limits

**Files:**

- `agents/langgraph/react_agent/main.py` -- `recursion_limit: 10`
- `agents/langgraph/agentic_rag/main.py` -- `recursion_limit: 15`
- Other LangGraph agents vary

These should be configurable via environment variable with sensible defaults.

#### 17. Missing HOME Env Var in Some Dockerfiles

**Files:**

- `agents/google/adk/Dockerfile` -- no `HOME` set
- `agents/langgraph/react_with_database_memory/Dockerfile` -- no `HOME` set
- `agents/langgraph/human_in_the_loop/Dockerfile` -- no `HOME` set

Other UBI9 Dockerfiles set `ENV HOME=/opt/app-root`. Omitting it can cause issues with libraries that write to `$HOME`.

#### 18. No HEALTHCHECK in Dockerfiles

**Files:** All 11 Dockerfiles

No Dockerfile includes a `HEALTHCHECK` instruction. While Kubernetes probes handle this at the orchestration layer, adding `HEALTHCHECK` improves standalone container runs (e.g., local `podman run` without Kubernetes).

#### 19. .dockerignore Inconsistencies

- `agents/autogen/mcp_agent/mcp_automl_template/` has **no** `.dockerignore`
- `agents/a2a/langgraph_crewai_agent/.dockerignore` uses a significantly different pattern from other agents

#### 20. A2A Chart Probe Config Naming Differs from Shared Chart

**Files:**

- `charts/agent/values.yaml` -- uses `healthCheck.path`, `healthCheck.livenessInitialDelay`
- `charts/a2a-langgraph-crewai/values.yaml` -- uses `probes.crew.livenessInitialDelay`, `probes.langgraph.*`

While the A2A chart is inherently different (two deployments), the naming convention diverges unnecessarily.

---

### Additional Issues (identified 2026-04-13)

#### 21. A2A Chart Hardcodes All Resource Names

**Directory:** `charts/a2a-langgraph-crewai/templates/`

All templates use literal strings (`a2a-crew-agent`, `a2a-langgraph-agent`) instead of Helm `{{ include }}` helpers. The chart is not reusable for multiple releases with different names. Contrast with `charts/agent/` which properly uses `_helpers.tpl` and `{{ include "agent.fullname" . }}`.

**Affected files:**

- `templates/deployment-crew.yaml` (line 5: `name: a2a-crew-agent`)
- `templates/deployment-langgraph.yaml` (line 5: `name: a2a-langgraph-agent`)
- `templates/service-crew.yaml` (line 4: `name: a2a-crew-agent`)
- `templates/service-langgraph.yaml` (line 4: `name: a2a-langgraph-agent`)
- `templates/route-crew.yaml` (line 4: `name: a2a-crew-agent`)
- `templates/route-langgraph.yaml` (line 4: `name: a2a-langgraph-agent`)

#### 22. A2A Chart Hardcodes replicaCount

**Files:**

- `charts/a2a-langgraph-crewai/templates/deployment-crew.yaml` (line 10: `replicas: 1`)
- `charts/a2a-langgraph-crewai/templates/deployment-langgraph.yaml` (line 10: `replicas: 1`)

Hardcoded to `1` instead of using `{{ .Values.replicaCount }}`. The shared chart uses a templated value, allowing scaling via values override.

#### 23. A2A Agent `values.yaml` Is Effectively Empty

**File:** `agents/a2a/langgraph_crewai_agent/values.yaml`

Contains only a comment -- no `nameOverride`, no env defaults, no documentation of available options. The Makefile compensates with `--set-string` flags, but this breaks the self-documenting pattern all other agents follow.

#### ~~24. `POSTGRES_PASSWORD` Missing from `react_with_database_memory/values.yaml`~~ ✅ NOT AN ISSUE

**Status:** Accepted — `POSTGRES_PASSWORD` is correctly handled as a secret, not an env var. The shared chart declares `secrets.postgresPassword: ""` in `charts/agent/values.yaml`, and the Makefile passes it via `.helm-secrets.yaml`. It should **not** appear in the agent's `env:` section.

#### 25. A2A Uses `template.env` Instead of `.env.example`

**File:** `agents/a2a/langgraph_crewai_agent/template.env`

Every other agent uses `.env.example`. Non-standard naming breaks the `make init` pattern and discoverability.

#### 26. Langflow `agent.yaml` Has No Env Section

**File:** `agents/langflow/simple_tool_calling_agent/agent.yaml`

The `.env.example` defines PostgreSQL and Langfuse variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `LANGFUSE_ADMIN_PASSWORD`, `LANGFUSE_ENCRYPTION_KEY`), but `agent.yaml` doesn't list them. This breaks the cross-referencing contract between `agent.yaml` and `.env.example`.

#### 27. Shared Chart `values.yaml` Missing `nameOverride`/`fullnameOverride` Defaults

**File:** `charts/agent/values.yaml`

`_helpers.tpl` supports both `nameOverride` and `fullnameOverride`, but the chart's `values.yaml` doesn't declare them. Standard Helm practice is to include `nameOverride: ""` / `fullnameOverride: ""` for discoverability and documentation.

#### ~~28. `mcp_automl_template` Dockerfile Uses GID `appuser` Instead of GID 0~~ ✅ RESOLVED

**Resolved in:** PR #56. Dockerfile rebuilt with UBI9 base, `chown -R 1001:0` + `chmod -R g=u`, proper `HOME=/opt/app-root`, `PYTHONPATH=/opt/app-root/src`, and `uv pip install --no-cache .`.

---

### Additional Issues (identified 2026-04-14)

#### High Priority

##### 29. A2A Chart Deployments Missing Security Contexts

**Files:**

- `charts/a2a-langgraph-crewai/templates/deployment-crew.yaml`
- `charts/a2a-langgraph-crewai/templates/deployment-langgraph.yaml`

Both A2A deployment templates completely lack pod-level and container-level security contexts. The shared `charts/agent/` chart includes:

- `securityContext.runAsNonRoot: true` (pod level)
- `allowPrivilegeEscalation: false` and `capabilities.drop: [ALL]` (container level)

The A2A chart has neither. Containers could potentially run as root with elevated privileges on clusters that don't enforce Pod Security Standards.

##### 30. A2A Secret Missing `quote` After `b64enc`

**File:** `charts/a2a-langgraph-crewai/templates/secret.yaml` (line 10)

```yaml
# A2A chart (broken):
api-key: {{ .Values.secrets.apiKey | b64enc }}

# Shared chart (correct):
api-key: {{ .Values.secrets.apiKey | b64enc | quote }}
```

Without `| quote`, base64 values containing special characters can produce malformed YAML. The shared chart correctly quotes all base64-encoded values.

##### ~~31. Empty `image.repository` Renders Invalid Image References~~ ✅ PARTIALLY RESOLVED

**Resolved in:** PR #63 — added `{{ required }}` validation on `image.repository` in shared Helm chart (`charts/agent/templates/deployment.yaml`). Helm now fails with a clear error message instead of rendering `":latest"`.

**Still open for A2A chart:** `charts/a2a-langgraph-crewai/` still has no `{{ required }}` validation on `image.crew.repository` and `image.langgraph.repository`.

#### Medium Priority

##### 32. A2A `requires-python` Missing Upper Bound

**File:** `agents/a2a/langgraph_crewai_agent/pyproject.toml` (line 6)

```toml
requires-python = ">=3.12"
```

All other agents specify an upper bound (`<3.14` or `<=3.14`). The A2A agent could run on Python 3.15+ where it may hit incompatibilities.

##### ~~33. FastAPI Version Fragmentation~~ ✅ RESOLVED

**Resolved in:** This branch. All 9 standard agents standardized to `fastapi>=0.135.1`.

##### ~~34. Uvicorn Version Mismatch~~ ✅ PARTIALLY RESOLVED

**Resolved in:** This branch — `mcp_automl_template/pyproject.toml` bumped from `>=0.30.0,<1.0.0` to `>=0.41.0,<1.0.0`. A2A agent (`>=0.30.0`) still unaddressed (non-standard agent, deferred).

##### 35. A2A `agent.yaml` / `template.env` Env Var Mismatch

**Files:**

- `agents/a2a/langgraph_crewai_agent/agent.yaml`
- `agents/a2a/langgraph_crewai_agent/template.env`

`agent.yaml` declares optional vars `CONTAINER_IMAGE_CREW` and `CONTAINER_IMAGE_LANGGRAPH` that are absent from `template.env`. Conversely, `template.env` contains `CREW_A2A_PORT`, `CREW_A2A_PUBLIC_URL`, `CREW_A2A_URL`, `LANGGRAPH_A2A_PORT`, `LANGGRAPH_A2A_PUBLIC_URL` that are undeclared in `agent.yaml`. This breaks the cross-referencing contract.

##### ~~36. Standardize Makefile `run-app` Host Binding~~ ✅ RESOLVED

**Resolved in:** This branch. All 9 agents now consistently bind to `127.0.0.1` for local dev (DNS rebinding protection). Container Dockerfiles remain at `0.0.0.0` for K8s networking.

##### 37. A2A Pod Templates Missing Standard Kubernetes Labels

**Files:**

- `charts/a2a-langgraph-crewai/templates/deployment-crew.yaml` (line 17)
- `charts/a2a-langgraph-crewai/templates/deployment-langgraph.yaml` (line 17)

Pod template metadata only includes `app: a2a-crew-agent` / `app: a2a-langgraph-agent`. The `a2a.labels` helper (which includes `app.kubernetes.io/managed-by` and `app.kubernetes.io/part-of`) is applied to deployment metadata but not to pod templates. Missing `app.kubernetes.io/name` and `app.kubernetes.io/instance` reduces observability and tooling compatibility.

##### ~~38. `.PHONY` Mismatch in Google ADK Makefile~~ ✅ RESOLVED

**Resolved in:** PR #63. Corrected `llama` → `llama-server` in `.PHONY` declaration.

##### 39. Optional Env Vars in `agent.yaml` Not Documented in `.env.example`

**Files:** 8 agent directories

- 8 agents declare `PORT` as optional in `agent.yaml` but don't include it in `.env.example`
- 4 agents declare `CONTAINER_IMAGE` as optional in `agent.yaml` but don't include it in `.env.example`

While these are optional variables, omitting them from `.env.example` makes them less discoverable.

##### 40. CrewAI Version Inconsistency

**Files:**

- `agents/a2a/langgraph_crewai_agent/pyproject.toml` -- `crewai[litellm]>=1.10.1`
- `agents/crewai/websearch_agent/pyproject.toml` -- `crewai[litellm]>=1.11.0`

The websearch agent requires a newer CrewAI minimum than the A2A agent.

#### Low Priority

##### 41. Suspicious Default Credentials in Langflow `.env.example`

**Files:**

- `agents/langflow/simple_tool_calling_agent/.env.example` (line 2-4)
- `agents/langflow/simple_tool_calling_agent/local/.env.example` (line 3)

```text
POSTGRES_USER=langflow
POSTGRES_PASSWORD=langflow
```

Using identical username and password is a security anti-pattern even for example files. Other agents use `not-needed-for-local-development` or clearly placeholder values.

##### 42. TODO Comments in Langflow Flow JSON

**File:** `agents/langflow/simple_tool_calling_agent/flows/outdoor-activity-agent.json`

Contains embedded TODO comments in Python code blocks:

- `# TODO: This is a temporary fix to avoid message duplication. We should develop a function for this.`
- `# TODO: Agent Description Depreciated Feature to be removed`

Indicates incomplete refactoring work.

##### 43. `chardet` Version Pinning Inconsistency

**Files:** Various `pyproject.toml`

- Exact pin: `chardet==7.2.0` (langgraph/agentic_rag, langgraph/human_in_the_loop)
- Range: `chardet>=7.1.0` (langgraph/react_agent, langgraph/react_with_database_memory)
- Bare: `chardet` with no version (google/adk)

##### 44. Inconsistent Help Text Column Width in Makefiles

**Files:** All agent Makefiles

Help target formatting varies: `%-12s` (most), `%-14s` (agentic_rag, autogen), `%-18s` (a2a). Minor cosmetic inconsistency.

##### 45. Incorrect Relative Path in `docs/local-development.md`

**File:** `docs/local-development.md`

References `mkdir -p ../../../milvus_data` which assumes the wrong nesting depth from an agent directory. The correct path would be `../../milvus_data` when running from a standard 3-level-deep agent directory.

##### ~~46. `env` Target Dependency Inconsistency in Makefiles~~ ✅ RESOLVED

**Resolved in:** This branch. Removed `init` dependency from `env` target in `react_with_database_memory/Makefile`.

##### ~~47. CONTRIBUTING.md Commit Scope Format Inconsistency~~ ✅ RESOLVED

**Resolved in:** PR #57. Scope format clarified with explicit examples and consistent notation.

### Additional Issues (identified 2026-04-17)

#### Low Priority

##### 53. Unnecessary `pymilvus`/`milvus-lite` in 6 Agent `pyproject.toml` Files

**Files:**

- `agents/langgraph/react_agent/pyproject.toml`
- `agents/langgraph/agentic_rag/pyproject.toml`
- `agents/langgraph/human_in_the_loop/pyproject.toml`
- `agents/langgraph/react_with_database_memory/pyproject.toml`
- `agents/google/adk/pyproject.toml`

No agent imports `pymilvus` or `milvus-lite` in its Python code. These dependencies are only needed by the Llama Stack server (`run_llama_server.yaml` configures `inline::milvus` as a vector_io provider). They should be installed in the `llama-server` Makefile target (as done in `agents/autogen/mcp_agent/Makefile`), not bundled as application dependencies. This adds unnecessary bloat to container images and increases the attack surface.

Note: `agents/langgraph/agentic_rag/pyproject.toml` also lists `langchain-milvus==0.3.3` — this may be legitimately needed if the RAG pipeline uses LangChain's Milvus vector store integration at runtime, but should be verified.

---

### GitHub Issue #45: Makefile & README Alignment Audit (identified 2026-04-15)

**Reference:** [red-hat-data-services/agentic-starter-kits#45](https://github.com/red-hat-data-services/agentic-starter-kits/issues/45)
**Reference pattern:** `agents/google/adk/Makefile` (PR #39)

#### Acceptance Criteria Status

| Criteria | Status | Notes |
|----------|--------|-------|
| Root README reflects framework directory structure | ✅ Complete | All 11 agents in table and directory tree (PR #63) |
| Agent READMEs replace old bash scripts with Helm instructions | ✅ Complete | All agent READMEs reference `make` targets and Helm workflow |
| `oc login` and `docker login` in agent READMEs | ✅ Complete | Present in all deployable agent READMEs |
| Local LLM setup (Ollama/llama-server) in agent READMEs | ✅ Complete | All applicable agents document `make ollama` and `make llama-server` |
| Standardized Makefile targets across all agents | ⚠️ Partial | 8/11 agents aligned; AutoGen, A2A, Langflow diverge (see #49, #50) |
| `make deploy` handles stale secrets on redeploy | ✅ Complete | `checksum/secret` annotation added to shared chart (PR #63). A2A chart still lacks annotation. |

#### Makefile Target Alignment Matrix

Reference pattern: `agents/google/adk/Makefile` (PR #39)

| Target | LG react | LG rag | LG hitl | LG db_mem | CrewAI | LlamaIdx | Vanilla | ADK | AutoGen | A2A | Langflow |
|--------|:--------:|:------:|:-------:|:---------:|:------:|:--------:|:-------:|:---:|:-------:|:---:|:--------:|
| init | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| re-init | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| env | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| ollama | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ |
| llama-server | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ |
| run-app | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| run-app-fresh | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| run-cli | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| build | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| push | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| build-openshift | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| deploy | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| undeploy | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| test | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| dry-run | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

**Legend:** ✓ = Present and matches reference, ✗ = Missing

**Fully aligned (8):** All 4 LangGraph agents, CrewAI, LlamaIndex, Vanilla Python (intentional ollama/llama-server omission), Google ADK

**Partially aligned (2):** AutoGen mcp_agent (missing 7 standard targets, has 5 non-standard), A2A (missing 5 standard targets, has 2 non-standard)

**Intentionally different (1):** Langflow (podman-compose model, standard targets not applicable)

#### High Priority

##### ~~48. Root README Repository Structure Tree Missing Agents and Charts~~ ✅ RESOLVED

**Resolved in:** PR #63 (`fix: update root README, and harden Helm chart`). Directory tree updated with `google/`, `a2a/`, `human_in_the_loop/`, and `charts/a2a-langgraph-crewai/`.

#### Medium Priority

##### 49. AutoGen `mcp_agent` Makefile Missing Standard Targets

**File:** `agents/autogen/mcp_agent/Makefile`

Missing from the google/adk reference pattern:

- `env` — no venv creation target
- `re-init` — no venv reload target
- `run-app` / `run-app-fresh` — uses `run` instead (and binds to `127.0.0.1`, see #36)
- `run-cli` — no CLI chat target
- `ollama` / `llama-server` — no local LLM targets

Has non-standard targets: `run-mcp`, `interact-mcp`, `deploy-mcp`, `undeploy-mcp`, `dry-run-mcp` (dual deployment model requires these, but standard targets should also exist).

##### 50. A2A Agent Makefile Missing Standard Targets

**File:** `agents/a2a/langgraph_crewai_agent/Makefile`

Missing from the google/adk reference pattern:

- `build-openshift` — no in-cluster build support
- `test` — no test target (no `tests/` directory either)
- `ollama` / `llama-server` — no local LLM targets
- `run-cli` — no CLI chat target

Has non-standard targets: `run-crew`, `run-langgraph` (dual-agent model requires these).

##### ~~51. `make deploy` Does Not Handle Stale Secrets on Redeployment~~ ✅ RESOLVED

**Resolved in:** PR #63. Added `checksum/secret` annotation to `charts/agent/templates/deployment.yaml` pod template (Option B — idiomatic Helm, zero-downtime). Pods now auto-restart when secret values change.

**Still open for A2A chart:** `charts/a2a-langgraph-crewai/templates/deployment-crew.yaml` and `deployment-langgraph.yaml` still lack the `checksum/secret` annotation.

##### 52. Vanilla Python Agent Missing Local LLM Targets

**File:** `agents/vanilla_python/openai_responses_agent/Makefile`

Missing `ollama` and `llama-server` targets. While this agent is designed to work with external APIs, it can also work with local LLMs via Ollama/Llama Stack if `BASE_URL` is pointed at `http://localhost:8321/v1`. Adding these targets maintains consistency with the standard pattern.

---

## GitHub Issues Cross-Reference

| GitHub Issue | Status | Audit Issues Covered |
|--------------|--------|---------------------|
| [#45](https://github.com/red-hat-data-services/agentic-starter-kits/issues/45) — Makefile & README alignment | Open | #1, #48, #49, #50, #51, #52 |
| [#28](https://github.com/red-hat-data-services/agentic-starter-kits/issues/28) — Stable dependency versions | Open | #9, #33, #34, #40, #43 |
| [#33](https://github.com/red-hat-data-services/agentic-starter-kits/issues/33) — Add Ruff to CI | Open | (code quality, not covered in audit) |
| [#14](https://github.com/red-hat-data-services/agentic-starter-kits/issues/14) — Migrate to uv + PEP 621 | Closed | (completed) |

---

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| **High** | 1 | PORT default mismatch (accepted as intentional: 8000 local, 8080 deploy), A2A missing security contexts, A2A secret quoting |
| **Medium** | 15 | A2A wrong base image, A2A unpinned uv, pymilvus versions (deferred), Langflow, A2A chart gaps, hardcoded chart names, empty A2A values, non-standard env file, Python version bounds, A2A env var mismatch, A2A pod labels, undocumented optional env vars, CrewAI version inconsistency, AutoGen Makefile alignment (separate branch), A2A Makefile alignment, Vanilla Python missing LLM targets |
| **Low** | 15 | Duplicate endpoints, unused deps, LOG_LEVEL, hardcoded limits, Dockerfile gaps, A2A replicaCount, Langflow agent.yaml env section, suspicious credentials, TODO comments, chardet pinning, help text formatting, docs path error, unnecessary pymilvus/milvus-lite in pyproject.toml |
| **Accepted** | 4 | ~~#2~~ PORT mismatch (intentional: 8000 local / 8080 deploy), ~~#8~~ AutoGen response format (by design), ~~#24~~ POSTGRES_PASSWORD (correctly handled as secret), ~~#27~~ shared chart nameOverride (not needed) |
| **Resolved** | 14 | ~~#1~~ README table, ~~#4~~ raw k8s manifests, ~~#5~~ health check 503, ~~#10~~ generic secrets, ~~#28~~ mcp_automl Dockerfile, ~~#31~~ image.repository validation, ~~#33~~ FastAPI version, ~~#34~~ uvicorn version (partial), ~~#36~~ 127.0.0.1 binding, ~~#38~~ ADK .PHONY, ~~#46~~ env:init dependency, ~~#47~~ commit scope, ~~#48~~ README tree, ~~#51~~ stale secrets |
| **Total** | **31 open** (+ 14 resolved, 4 accepted) | |

---

## Existing Migration Plans

A detailed plan to address issues #4, #6, #7, #10, #19, and #28 exists at `docs/superpowers/plans/2026-04-08-mcp-automl-helm-migration.md` with a corresponding design spec at `docs/superpowers/specs/2026-04-08-mcp-automl-helm-migration-design.md`. This plan was **partially executed in PR #56**, resolving issues #4, #10, and #28, and partially fixing #6 and #7 (mcp_automl_template only; A2A Dockerfile still unaddressed). Issue #19 (`.dockerignore` for mcp_automl_template) remains open.

---

## Design Decisions (Intentional Divergences)

These are not issues -- they are deliberate architectural choices:

1. **A2A chart is separate from shared chart** -- dual-agent orchestration with two-phase deployment requires a dedicated chart. Should not be merged into `charts/agent/`.
2. **Langflow has no Helm integration** -- it's a flow-import agent (`deploymentModel: flow-import`), not a containerized service. Correctly follows `docs/adding-a-new-agent.md` guidelines.
3. **react_with_database_memory has extra `database_connected` field** in health response -- intentional for database-backed agents.
4. **A2A uses `/.well-known/agent-card.json`** for health checks -- aligns with A2A agent discovery protocol standards.
