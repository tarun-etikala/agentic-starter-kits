# Skill Changefile: add-behavioral-tests — Langflow Support

This document records every change needed to the `add-behavioral-tests` skill
(SKILL.md, eval-criteria-btest-validate.json, mlflow-procedures.json) to
support Langflow non-standard agents. Apply these changes to the skill source
once the behavioral tests PR is merged.

Jira: RHAIENG-5390
Agent: `agents/langflow/simple_tool_calling_agent`

All changes are gated on `agent.yaml` having `deploymentModel: flow-import`
or `framework: langflow`. Standard agent behavior is unaffected.

---

## 1. SKILL.md Changes

### Phase 1: Remove non-standard agent hard stop

**Current text (around "Phase 1: Investigate the Agent and Cluster" → step 2):**
```
Check if the agent is non-standard (see AGENTS.md — langflow and a2a agents
diverge significantly). If it lacks `main.py`, `src/`, or standard Makefile
targets, stop and tell the user that this workflow does not yet support
non-standard agents.
```

**Replace with:**
```
Check if the agent is non-standard (see AGENTS.md). Read `agent.yaml`:

- If `deploymentModel: flow-import` (Langflow agents): Enter the Langflow
  investigation path. These agents have no `main.py`, `src/`, `Dockerfile`,
  or standard Makefile targets. Instead:
  - **Tools**: Extract from the flow JSON file (`flows/*.json`) — tool
    definitions are embedded in flow component nodes.
  - **Response format**: Uses `/api/v1/run/{flow_id}` (supported by runner.py
    via `api_format="langflow_run"` from RHAIENG-5389).
  - **System prompt**: Embedded in the flow JSON agent/prompt component nodes.
  - **Streaming**: Always `stream=false` — Langflow `/api/v1/run` does not
    support streaming for tool extraction.
  - **Deployment**: Langflow agents are pre-deployed via flow-import (not
    Helm). Skip `/deploy-agents` — verify deployment via `oc get pods` and
    `curl /health` on the Langflow route.
  - **Flow ID**: Discover dynamically via `GET /api/v1/flows/` with a Bearer
    token from `GET /api/v1/auto_login`. Record in `LANGFLOW_FLOW_ID`.
  - **Tracing**: Uses Langfuse (not MLflow). Tool calls come from HTTP
    response `content_blocks`, not MLflow traces.

- If the agent lacks `main.py`, `src/`, or standard Makefile targets AND is
  NOT a Langflow agent: stop and tell the user that this workflow does not
  yet support this type of non-standard agent.
```

### Phase 1: Deployment gate change

**Current text (Phase 1 gate):**
```
**Gate**: `agentic-starter-kits-skills:add-behavioral-tests.phase-1-deploy` —
consult eval-criteria. If the agent was not already deployed, verify that
`/agentic-starter-kits-skills:deploy-agents` was invoked (not manual
`make deploy`).
```

**Append:**
```
**Langflow exception**: For `deploymentModel: flow-import` agents, this gate
passes if the Langflow pod is running and `/health` returns 200. The
`/deploy-agents` check is waived — Langflow uses flow-import deployment.
```

### Phase 2: Conditional MLflow skip

**Current text (Phase 2 header area):**
```
**Goal**: Confirm that the agent already has MLflow tracing integrated.
```

**Prepend before Phase 2 body:**
```
**Langflow exception**: If `framework: langflow` in `agent.yaml`, skip Phase 2
entirely. Langflow agents use Langfuse for tracing, and tool calls are
extracted from the HTTP response `content_blocks` by the harness runner
(`_extract_langflow_tool_calls()`). No MLflow verification or bug filing is
needed. Set `tracing_source = "content_blocks"` for downstream phases.
```

### Phase 4: Langflow conftest pattern

**After the existing conftest.py section, add:**
```
#### Langflow-specific conftest pattern

For `framework: langflow` agents, the conftest differs from standard agents:

1. **No MLflow enrichment block** — remove the entire
   `if mlflow is not None and result.success: ...` section. Tool calls are
   already populated by the runner's `_extract_langflow_tool_calls()`.
2. **Additional env var**: `LANGFLOW_FLOW_ID` for the flow ID.
3. **TaskConfig**: Include `api_format="langflow_run"` and `flow_id=FLOW_ID`.
4. **No `MLflowTraceClient` import** — not needed.
5. **`STREAM = False`** always — no streaming classification needed.
6. **Evidence constants**: Match actual response content from external APIs
   (e.g., "forecast", "°c", "national") — not tool names.

Example:

```python
config = TaskConfig(
    agent_url=agent_url,
    query=query,
    expected_tools=expected_tools,
    timeout_seconds=timeout_seconds,
    stream=False,
    api_format="langflow_run",
    flow_id=FLOW_ID,
)
result = await run_task(config, client=http_client)
return result  # tool_calls already populated from content_blocks
```
```

### Phase 6: Langflow EvalHub parameters

**After the existing EvalHub fixture section, add:**
```
#### Langflow EvalHub configuration

For `framework: langflow` agents, the EvalHub job config YAML must include
`api_format` and `flow_id` parameters:

```yaml
parameters:
  api_format: langflow_run
  flow_id: ${LANGFLOW_FLOW_ID}
```

The adapter's `_get_langflow_token()` handles auth automatically.
```

### Phase 7: Skip for Langflow

**After the existing Phase 7 text, add:**
```
**Langflow exception**: Skip Phase 7 entirely for `framework: langflow`
agents. They use Langfuse for tracing, not MLflow. There are no MLflow
Helm flags to check.
```

### Phase 9: Langflow deployment verification

**After the existing Phase 9 text, add:**
```
**Langflow exception**: For `deploymentModel: flow-import` agents, do NOT
use `/deploy-agents`. Langflow agents are pre-deployed via flow-import.
Verify deployment with:

1. Pod running: `oc get pods -n <langflow-namespace>`
2. Health check: `curl -sf https://<route>/health`
3. Smoke query via `/api/v1/run/{flow_id}` (not `/chat/completions`)

If unhealthy, notify the user — Langflow redeployment requires flow
re-import, not `make deploy`.
```

### Phase 10: Langflow E2E block

**After the existing E2E script instructions, add:**
```
#### Langflow E2E additions

The Langflow E2E block requires:
- **Route discovery**: `oc get route -n langflow-agent langflow`
  (separate namespace from standard agents)
- **Flow ID discovery**: `GET /api/v1/flows/` with Bearer token
- **Auth token**: `GET /api/v1/auto_login` for Bearer token
- **Job YAML**: Include `api_format: langflow_run` and `flow_id` parameters
- **Conditional execution**: Guard with `if [[ -f eval-langflow-*.yaml ]]`
  so the script doesn't fail if Langflow is not deployed
```

### Phase 11: Langflow validation exceptions

**Add to Phase 11b:**
```
**Langflow exception**: This gate is WAIVED for `framework: langflow` agents.
Tool calls come from HTTP response `content_blocks` (via
`_extract_langflow_tool_calls()` in runner.py), not from MLflow trace
enrichment. No enrichment warning check is needed. The gate passes if
`result.tool_calls` is non-empty after `run_task()` returns.
```

**Add to Phase 11c, 11f, 11g:**
```
**Langflow exception**: SKIP for `framework: langflow` agents. These agents
use Langfuse for tracing, not MLflow. There are no MLflow traces to inspect.
```

**Modify Phase 11j cross-agent consistency check, point 2:**
```
Current: "MLflow enrichment uses asyncio.to_thread + try/except +
logging.warning() + warnings.warn() — all four elements"

Add: "Exception: Langflow agents have NO MLflow enrichment block in
conftest.py — this is correct and expected. The consistency check should
verify that Langflow conftest uses api_format='langflow_run' and flow_id
instead."
```

### Definition of Done: Add Langflow-aware items

**Modify the Phase 11b checkbox:**
```
Current: "Phase 11b: tool_calls enrichment gate passed (or waived with
bug ticket if tracing is missing)"

Change to: "Phase 11b: tool_calls enrichment gate passed (or waived with
bug ticket if tracing is missing, or waived for Langflow agents where
tool_calls come from content_blocks)"
```

---

## 2. eval-criteria-btest-validate.json Changes

### Pre-gate: Standard agent pattern check

**Current assertion:**
```json
{
  "id": "standard-agent-pattern",
  "description": "Agent directory has main.py (standard agent pattern)",
  "type": "exec",
  "command": "test -f agents/{framework}/{agent}/main.py"
}
```

**Change to:**
```json
{
  "id": "agent-pattern-check",
  "description": "Agent matches a supported pattern (standard or Langflow)",
  "type": "eval",
  "criteria": "Standard agents have main.py; Langflow agents have agent.yaml with deploymentModel: flow-import and a flows/ directory. At least one pattern must match."
}
```

### phase-1-deploy gate: Langflow exception

**Add assertion:**
```json
{
  "id": "langflow-deploy-waiver",
  "description": "Langflow agents: deployment gate passes if pod is running and /health returns 200 (no /deploy-agents required)",
  "type": "eval",
  "criteria": "For framework=langflow: oc get pods shows langflow pod Running, curl /health returns 200. /deploy-agents check is waived.",
  "applies_when": "framework == langflow"
}
```

### phase-11b gate: Langflow waiver

**Add waiver condition to the phase-11b gate:**
```json
{
  "id": "langflow-content-blocks-waiver",
  "description": "Langflow agents extract tool_calls from content_blocks, not MLflow — enrichment gate waived",
  "type": "eval",
  "criteria": "For framework=langflow: result.tool_calls is non-empty after run_task() (populated by _extract_langflow_tool_calls). MLflow enrichment check is waived.",
  "waives": ["no-enrichment-warning", "scorer-execution", "enrichment-all-pass"],
  "applies_when": "framework == langflow"
}
```

### phase-11c, 11f, 11g gates: Skip for Langflow

**Add to each gate:**
```json
{
  "id": "langflow-no-mlflow-traces",
  "description": "Langflow uses Langfuse, not MLflow — trace structure check skipped",
  "type": "eval",
  "criteria": "Gate is skipped for framework=langflow. No MLflow traces to verify.",
  "applies_when": "framework == langflow",
  "result": "SKIP"
}
```

### phase-11j: Cross-agent consistency exception

**Modify assertion 2 (MLflow enrichment pattern):**
```json
{
  "id": "mlflow-enrichment-pattern",
  "description": "conftest.py MLflow enrichment uses all 4 elements",
  "exception": "Langflow agents have no MLflow enrichment block — verify they use api_format='langflow_run' and flow_id instead"
}
```

---

## 3. mlflow-procedures.json Changes

**No changes needed.** The MLflow procedures are only used for MLflow-tracing
agents. Langflow agents skip all MLflow verification phases, so these
procedures are never invoked for them.

---

## Summary of Changes

| File | Sections changed | Nature |
|------|-----------------|--------|
| SKILL.md | Phase 1, 2, 4, 6, 7, 9, 10, 11b/c/f/g/j, DoD | Conditional branches for Langflow |
| eval-criteria JSON | pre, phase-1-deploy, 11b, 11c, 11f, 11g, 11j | Waiver/skip conditions for Langflow |
| mlflow-procedures JSON | None | No changes needed |

All changes are additive — they add conditional exceptions for
`framework: langflow` / `deploymentModel: flow-import` agents without
modifying the existing standard agent workflow.

---

## 4. Validation Observations (from RHAIENG-5390 implementation)

These are notes from actually running the workflow for the Langflow agent,
useful when implementing the skill changes:

### Golden query expected_elements must match agent vocabulary
External APIs (Open-Meteo, NPS) return live data. The agent does NOT always
use the exact keywords you expect. For example:
- The agent says "23°C" and "high/low", NOT the word "temperature"
- The agent says "national monument" or "national park" interchangeably
- Use broad structural terms: "forecast", "national", "utah" — not
  "temperature", "park"

### Langflow route is in a separate namespace
Unlike standard agents (all in one namespace), the Langflow agent runs in
`langflow-agent` namespace. The E2E script must use a separate
`LANGFLOW_NAMESPACE` variable for route discovery.

### Flow ID is dynamic
The flow ID (`fadd303c-...`) changes on every re-import. The skill should
instruct discovering it via `GET /api/v1/flows/` rather than hardcoding.
The auto_login token is needed for this API call.

### Langflow latency is 2-3x standard agents
Due to flow execution overhead + external API calls (Open-Meteo, NPS),
typical latency is 6-15s per query vs 2-5s for standard agents. The
`max_latency_p95` threshold should be 30s (vs 8-15s for standard agents).
The `PASS_K_TIMEOUT` should be 90s (vs 60s).

### mlflow_run_id is non-null even for Langflow
The EvalHub adapter logs an MLflow run for ALL agents, including Langflow.
The `mlflow_run_id` in the job results is from the adapter's run logging
(metrics/scores), NOT from agent-side tracing. This means Phase 11f
("mlflow_run_id must be non-null for ALL agents") passes without waiver
for Langflow. The skill's Phase 11f Langflow exception should note this
distinction: the run ID comes from adapter logging, not agent traces.

### Content_blocks tool extraction is reliable
The Langflow adapter (`_extract_langflow_tool_calls()`) reliably extracts
tool calls from `content_blocks`. In all 17 test runs (including 16
pass@k iterations), tool_calls were always populated — no fallback to
content heuristics was needed. This validates the Phase 11b waiver approach.

### EvalHub E2E requires separate namespace handling
The E2E script's Langflow block should be conditional (`if [[ -f ... ]]`)
since the Langflow agent may not be deployed on all clusters. The route
discovery, flow ID lookup, and auth token acquisition add ~2s overhead
to the preflight checks.
