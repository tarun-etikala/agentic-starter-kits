# Create the Tracing Module (`tracing.py`)

> **Usage:** `/project:create-tracing-module <agent_path>`
> **Example:** `/project:create-tracing-module agents/autogen/chat_agent`

You are creating the `tracing.py` file for a new agent template, following this repo's established patterns.

## Input

You need two pieces of information before proceeding:
1. **Agent path**: The agent directory (e.g., `agents/autogen/chat_agent/`)
2. **Autolog support report**: The output from the `check-autolog-support` skill, which classifies the framework as Level A, B, or C and identifies the autolog module(s) needed.

If either is missing, ask the user.

## Context

Read `tracing.md` at the repo root for the full tracing architecture, design principles, and how each existing agent integrates with MLflow.

## Reference Files

Read the reference `tracing.py` that matches the coverage level. These are the source of truth — follow their patterns exactly:

- **Level A — autolog variant** (full autolog): `agents/langgraph/react_agent/src/react_agent/tracing.py`
- **Level A — OTel variant** (framework emits OTel spans): `agents/google/adk/src/adk_agent/tracing.py`
- **Level B** (partial autolog): `agents/crewai/websearch_agent/src/crewai_web_search/tracing.py`
- **Level C** (no framework autolog): `agents/vanilla_python/openai_responses_agent/src/openai_responses_agent/tracing.py`

## What to Create

Create the file at: `<agent_path>/src/<package_name>/tracing.py`

The `<package_name>` is the Python package name — find it by looking at the existing `src/` directory or `pyproject.toml` `[tool.setuptools.packages.find]`.

## How to Build It

### Shared code (all levels)

Copy these **exactly** from the reference file — they are identical across all agents:
- Logger setup (module-level `logging.getLogger("tracing")` with handler)
- `check_mlflow_health()` function (retry loop with time budget)
- `enable_tracing()` skeleton (load_dotenv, MLFLOW_TRACKING_URI check, health check with graceful degradation, set_tracking_uri, set_experiment, enable_async_logging)

### Framework-specific code

The **only parts that differ** between levels are inside `enable_tracing()` and whether `wrap_func_with_mlflow_trace()` exists:

**Level A (autolog variant)** — Read the LangGraph reference. Adapt by:
- Replacing the `import mlflow.langchain` / `mlflow.langchain.autolog()` with the correct module for the new framework (from the autolog report)
- No `wrap_func_with_mlflow_trace()` needed

**Level A (OTel variant)** — Read the Google ADK reference. Use this when the framework has no `mlflow.<framework>.autolog()` but natively emits OpenTelemetry spans. Adapt by:
- Setting up `TracerProvider` with `OTLPSpanExporter` pointing at `{tracking_uri}/v1/traces`
- Passing the experiment ID via the `x-mlflow-experiment-id` header (get it from `mlflow.set_experiment()`)
- The MLflow server requires a SQL backend (`--backend-store-uri sqlite:///mlflow.db`)
- Extra package: `opentelemetry-exporter-otlp-proto-http`
- No `wrap_func_with_mlflow_trace()` needed

**Level B** — Read the CrewAI reference. Adapt by:
- Replacing the framework autolog module (e.g., `mlflow.crewai` → `mlflow.<new_framework>`)
- Adjusting the provider autolog routing if the new framework's LLM provider path differs. If the framework uses a single LLM path, simplify by hardcoding the provider autolog instead of the `provider_autolog_map` + `LLM_PROVIDER` routing
- Copying `wrap_func_with_mlflow_trace()` as-is (with `name` parameter)

**Level C** — Read the Vanilla Python reference. Adapt by:
- Replacing the provider autolog module if the framework uses a different LLM SDK (from the autolog report)
- Copying `wrap_func_with_mlflow_trace()` as-is

## Final Checklist

After creating the file, verify:
- [ ] Logger setup is at module level (not inside a function)
- [ ] `check_mlflow_health()` is identical to the reference
- [ ] `enable_tracing()` has graceful degradation (returns on unreachable server, doesn't crash)
- [ ] MLflow imports are lazy (inside `enable_tracing()` / `wrap_func_with_mlflow_trace()`, not at module top)
- [ ] `wrap_func_with_mlflow_trace()` returns the original function unchanged when `MLFLOW_TRACKING_URI` is not set
- [ ] The correct autolog module is used for the framework
- [ ] `enable_async_logging()` is called before autolog

## Self-Update (mandatory)

**Before finishing, you MUST check whether this skill file needs updating.** This is not optional. If any of the following are true, update this file immediately:

- You deviated from these instructions because they were inaccurate, outdated, or insufficient — and your deviation worked.
- You encountered a new pattern not covered here (e.g., a framework that uses OpenTelemetry instead of autolog, or a new provider path). Add it as a variant under the existing levels (A, B, or C) rather than introducing new levels.
- File paths, function names, or API patterns referenced here have changed.
- A step didn't work as described and needed a different approach.

If nothing needed changing, move on. But do not skip this check.
