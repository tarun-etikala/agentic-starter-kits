# Type Annotation Coverage & Comprehensive CI Type-Check (RHAIENG-4064)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reach ≥80% return-type annotation coverage across all agent `src/` and `main.py` files, and replace the CI type-check job (which ignores 8 error categories) with per-agent matrix runs that install dependencies and report all errors.

**Architecture:** Replace the single `ty check --ignore ...` CI job with a GitHub Actions matrix strategy that `uv sync`s each agent's deps into a `.venv`, then runs `ty check --python .venv` with zero `--ignore` flags. Add return-type annotations to all 233 unannotated functions across 11 agents and 1 component (current baseline: 188/421 = 44.7%).

**Tech Stack:** ty 0.0.51, uv 0.11.21, GitHub Actions matrix strategy, Python 3.12 type annotations

## Global Constraints

- Python ≥3.12, <3.14
- Use `uv` — never `pip` directly inside agent venvs
- Don't modify deployment charts, CONTRIBUTING.md, CI config beyond `code-quality.yml`, or root Makefile
- Don't refactor other agents when working on one agent
- Keep agents self-contained — no cross-agent imports
- Langflow agent is excluded (no Python source files in `src/`)
- `agents/openclaw/`, `agents/claude-code/`, `agents/codex/`, `agents/opencode/` have no Python source to check

---

### Task 1: CI workflow — per-agent matrix type-check with deps installed

**Files:**
- Modify: `.github/workflows/code-quality.yml:111-147`

**Interfaces:**
- Consumes: Each agent's `pyproject.toml` and `uv.lock`
- Produces: A matrix CI job that runs `ty check` per-agent with full dependency resolution and zero `--ignore` flags

- [ ] **Step 1: Replace the `type-check` job in `code-quality.yml`**

Replace lines 111–147 with the following matrix-based job:

```yaml
  type-check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        include:
          - name: langgraph-react
            path: agents/langgraph/templates/react_agent
            check: src/ main.py
          - name: langgraph-rag
            path: agents/langgraph/templates/agentic_rag
            check: src/ main.py
          - name: langgraph-hitl
            path: agents/langgraph/templates/human_in_the_loop
            check: src/ main.py
          - name: langgraph-dbmem
            path: agents/langgraph/templates/react_with_database_memory
            check: src/ main.py
          - name: google-adk
            path: agents/google/templates/adk
            check: src/ main.py
          - name: crewai-websearch
            path: agents/crewai/templates/websearch_agent
            check: src/ main.py
          - name: llamaindex-websearch
            path: agents/llamaindex/templates/websearch_agent
            check: src/ main.py
          - name: autogen-mcp
            path: agents/autogen/templates/mcp_agent
            check: src/ main.py
          - name: autogen-automl
            path: agents/autogen/templates/mcp_agent/mcp_automl_template
            check: mcp_server.py register_tools.py utils.py interact_with_mcp.py
          - name: a2a-langgraph-crewai
            path: agents/a2a/templates/langgraph_crewai_agent
            check: src/
          - name: vanilla-openai
            path: agents/vanilla_python/templates/openai_responses_agent
            check: src/ main.py
          - name: auth-component
            path: components/auth
            check: src/
    name: "ty (${{ matrix.name }})"
    steps:
      - name: Checkout
        uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10  # v6.0.3
        with:
          persist-credentials: false

      - name: Setup Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405  # v6.2.0
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39  # v8.2.0
        with:
          version: "0.11.21"
          enable-cache: true
          cache-dependency-glob: "${{ matrix.path }}/uv.lock"

      - name: Install dependencies
        working-directory: ${{ matrix.path }}
        run: uv sync --frozen

      - name: Install ty
        run: pip install ty==0.0.51

      - name: Run type-check
        working-directory: ${{ matrix.path }}
        run: ty check --python .venv ${{ matrix.check }}
```

- [ ] **Step 2: Verify the workflow YAML is valid**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/code-quality.yml'))"`
Expected: No errors

- [ ] **Step 3: Lint the workflow**

Run: `actionlint .github/workflows/code-quality.yml` (if installed) or verify manually that the YAML structure is correct.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/code-quality.yml
git commit -m "ci: replace ignoring ty check with per-agent matrix + dep install (RHAIENG-4064)"
```

---

### Task 2: Type annotations — langgraph/react_agent

**Files:**
- Modify: `agents/langgraph/templates/react_agent/src/react_agent/agent.py`
- Modify: `agents/langgraph/templates/react_agent/src/react_agent/tracing.py`
- Modify: `agents/langgraph/templates/react_agent/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent with zero ty errors

- [ ] **Step 1: Annotate `src/react_agent/agent.py`**

The `get_graph_closure` function already has `-> Any`. No changes needed in this file.

- [ ] **Step 2: Annotate `src/react_agent/tracing.py`**

Add return type to `enable_tracing`:
```python
# Line 63 — already has -> None. No change needed.
```

The `check_mlflow_health` function already has `-> None`. Both functions are annotated. No changes needed.

- [ ] **Step 3: Annotate `main.py`**

Add return types to these functions:

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 121 | `async def lifespan(app: FastAPI):` | `async def lifespan(app: FastAPI) -> AsyncIterator[None]:` |
| 174 | `def _build_langchain_messages(messages: list[ChatMessage]) -> list[HumanMessage]:` | Already annotated |
| 182 | `def _make_completion_id() -> str:` | Already annotated |
| 152 | `def _auth_enabled() -> bool:` | Already annotated |
| 156 | `def _configure_auth_middleware() -> None:` | Add `-> None` |
| 193 | `async def chat_completions(request: ChatCompletionRequest):` | `async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse \| StreamingResponse:` |
| 208 | `async def _handle_chat(messages: list[HumanMessage], model_id: str):` | `async def _handle_chat(messages: list[HumanMessage], model_id: str) -> dict[str, Any]:` |
| 283 | `async def _handle_stream(messages: list[HumanMessage], model_id: str):` | `async def _handle_stream(messages: list[HumanMessage], model_id: str) -> StreamingResponse:` |
| 290 | `async def event_generator():` | `async def event_generator() -> AsyncIterator[str]:` |
| 413 | `async def health():` | `async def health() -> HealthResponse \| JSONResponse:` |
| 434 | `async def playground():` | `async def playground() -> FileResponse:` |
| 442 | `async def serve_image(filename: str):` | `async def serve_image(filename: str) -> FileResponse:` |

Add necessary imports at the top of `main.py`:
```python
from collections.abc import AsyncIterator
from typing import Any
```

- [ ] **Step 4: Install deps and run ty check**

```bash
cd agents/langgraph/templates/react_agent
uv sync --frozen
ty check --python .venv src/ main.py
```
Expected: No errors (or only errors from third-party library stubs that need `# type: ignore` comments)

- [ ] **Step 5: Fix any ty errors**

If ty reports errors from framework-specific patterns (e.g., decorator return types), add targeted `# type: ignore[rule-name]` comments on the specific lines. Do not add blanket ignores.

- [ ] **Step 6: Commit**

```bash
git add agents/langgraph/templates/react_agent/
git commit -m "feat(react_agent): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 3: Type annotations — langgraph/agentic_rag

**Files:**
- Modify: `agents/langgraph/templates/agentic_rag/src/agentic_rag/agent.py`
- Modify: `agents/langgraph/templates/agentic_rag/src/agentic_rag/tools.py`
- Modify: `agents/langgraph/templates/agentic_rag/src/agentic_rag/tracing.py`
- Modify: `agents/langgraph/templates/agentic_rag/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/agentic_rag/agent.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 14 | `def get_graph_closure(...) -> Callable:` | Already annotated |
| 73 | `def agent_with_instruction(instruction_prompt: str \| None) -> Callable:` | Already annotated |
| 76 | `def agent(state: AgentState) -> dict:` | Already annotated (inside closure) |
| 98 | `def generate(state: AgentState):` | `def generate(state: AgentState) -> dict[str, list[AIMessage]]:` |
| 179 | `def get_graph(instruction_prompt: SystemMessage \| None = None):` | `def get_graph(instruction_prompt: SystemMessage \| None = None) -> CompiledStateGraph:` |

Add import: `from langgraph.graph.state import CompiledStateGraph` (already imported at line 6 via `StateGraph`, but `CompiledStateGraph` may need explicit import — check).

- [ ] **Step 2: Annotate `src/agentic_rag/tools.py`**

Check the file for unannotated functions. If `retriever_tool` is defined via a decorator, the decorator handles the type. Add return types to any helper functions.

- [ ] **Step 3: Annotate `src/agentic_rag/tracing.py`**

Same pattern as react_agent tracing. `check_mlflow_health` and `enable_tracing` should both have `-> None`. Check current state and add if missing.

- [ ] **Step 4: Annotate `main.py`**

Same pattern as Task 2 Step 3 — the `main.py` files share the same FastAPI template structure. Add return types to:
- `lifespan` → `AsyncIterator[None]`
- `_configure_auth_middleware` → `None`
- `chat_completions` → `ChatCompletionResponse | StreamingResponse`
- `_handle_chat` → `dict[str, Any]`
- `_handle_stream` → `StreamingResponse`
- `event_generator` (inner) → `AsyncIterator[str]`
- `health` → `HealthResponse | JSONResponse`
- `playground` → `FileResponse`
- `serve_image` → `FileResponse`
- `_auth_enabled` → `bool` (check if already present)
- `_build_langchain_messages` → check if already present

- [ ] **Step 5: Run ty check**

```bash
cd agents/langgraph/templates/agentic_rag
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 6: Commit**

```bash
git add agents/langgraph/templates/agentic_rag/
git commit -m "feat(agentic_rag): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 4: Type annotations — langgraph/human_in_the_loop

**Files:**
- Modify: `agents/langgraph/templates/human_in_the_loop/src/human_in_the_loop/agent.py`
- Modify: `agents/langgraph/templates/human_in_the_loop/src/human_in_the_loop/tools.py`
- Modify: `agents/langgraph/templates/human_in_the_loop/src/human_in_the_loop/tracing.py`
- Modify: `agents/langgraph/templates/human_in_the_loop/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/human_in_the_loop/agent.py`**

Check for unannotated functions. The `get_graph_closure` pattern is the same as react_agent. Add `-> Any` or the specific return type if identifiable.

- [ ] **Step 2: Annotate `src/human_in_the_loop/tracing.py`**

Add `-> None` to `enable_tracing` if missing. `check_mlflow_health` should already have `-> None`.

- [ ] **Step 3: Annotate `main.py`**

Same FastAPI template pattern. Add return types to all endpoint handlers and helper functions (same list as Task 2 Step 3).

- [ ] **Step 4: Run ty check**

```bash
cd agents/langgraph/templates/human_in_the_loop
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/langgraph/templates/human_in_the_loop/
git commit -m "feat(human_in_the_loop): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 5: Type annotations — langgraph/react_with_database_memory

**Files:**
- Modify: `agents/langgraph/templates/react_with_database_memory/src/react_with_database_memory/agent.py`
- Modify: `agents/langgraph/templates/react_with_database_memory/src/react_with_database_memory/tracing.py`
- Modify: `agents/langgraph/templates/react_with_database_memory/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/react_with_database_memory/agent.py`**

This agent has the most unannotated functions (0/6 in agent.py):

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 26 | `def _drop_orphaned_tool_messages(messages):` | `def _drop_orphaned_tool_messages(messages: list) -> list:` |
| 32 | `def wrap_model_call(self, request, handler):` | `def wrap_model_call(self, request: Any, handler: Any) -> Any:` |
| 39 | `async def awrap_model_call(self, request, handler):` | `async def awrap_model_call(self, request: Any, handler: Any) -> Any:` |
| 47 | `def get_graph_closure(...) -> Callable:` | Already annotated |
| 93 | `def get_graph(memory: BaseCheckpointSaver, thread_id=None, system_prompt=default_system_prompt) -> CompiledStateGraph:` | Add param type: `thread_id: str \| None = None, system_prompt: str = default_system_prompt` |

For `wrap_model_call` and `awrap_model_call`, use the actual types from `langchain.agents.middleware` if available, otherwise `Any`.

- [ ] **Step 2: Annotate `src/react_with_database_memory/tracing.py`**

Add `-> None` to `enable_tracing` if missing. Same pattern as other tracing files.

- [ ] **Step 3: Annotate `main.py`**

Same FastAPI template pattern. Add return types to all endpoint handlers.

- [ ] **Step 4: Run ty check**

```bash
cd agents/langgraph/templates/react_with_database_memory
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/langgraph/templates/react_with_database_memory/
git commit -m "feat(react_with_database_memory): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 6: Type annotations — google/adk

**Files:**
- Modify: `agents/google/templates/adk/src/adk_agent/agent.py`
- Modify: `agents/google/templates/adk/src/adk_agent/tracing.py`
- Modify: `agents/google/templates/adk/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/adk_agent/agent.py`**

Both `get_agent` and `get_runner` already have return type annotations (`-> LlmAgent` and `-> InMemoryRunner`). Verify no functions are missing.

- [ ] **Step 2: Annotate `src/adk_agent/tracing.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 19 | `def _safe_uri(uri: str) -> str:` | Already annotated |
| 30 | `def check_mlflow_health(...) -> None:` | Already annotated |
| 84 | `def wrap_func_with_mlflow_trace(...) -> Callable:` | Already annotated |
| 106 | `def enable_tracing() -> None:` | Already annotated |

Verify all functions are annotated. If the coverage script showed 2/4, re-check — the `_safe_uri` helper may not have been counted.

- [ ] **Step 3: Annotate `main.py`**

Same FastAPI template pattern. Add return types to all endpoint handlers and helper functions.

- [ ] **Step 4: Run ty check**

```bash
cd agents/google/templates/adk
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/google/templates/adk/
git commit -m "feat(adk): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 7: Type annotations — crewai/websearch_agent

**Files:**
- Modify: `agents/crewai/templates/websearch_agent/src/crewai_web_search/crew.py`
- Modify: `agents/crewai/templates/websearch_agent/src/crewai_web_search/tracing.py`
- Modify: `agents/crewai/templates/websearch_agent/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/crewai_web_search/crew.py`**

Read the file and add return types to unannotated functions. CrewAI uses decorators heavily — for `@task` and `@agent` decorated methods, the return type comes from the decorator. Add explicit return types anyway for clarity.

- [ ] **Step 2: Annotate `src/crewai_web_search/tracing.py`**

This tracing.py has `_TRACING_ENABLED` and 3 functions. Add `-> None` to `enable_tracing` if missing.

- [ ] **Step 3: Annotate `main.py`**

Same FastAPI template pattern.

- [ ] **Step 4: Run ty check**

```bash
cd agents/crewai/templates/websearch_agent
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/crewai/templates/websearch_agent/
git commit -m "feat(crewai_websearch): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 8: Type annotations — llamaindex/websearch_agent

**Files:**
- Modify: `agents/llamaindex/templates/websearch_agent/src/websearch_agent/agent.py`
- Modify: `agents/llamaindex/templates/websearch_agent/src/websearch_agent/tracing.py`
- Modify: `agents/llamaindex/templates/websearch_agent/src/websearch_agent/workflow.py`
- Modify: `agents/llamaindex/templates/websearch_agent/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/websearch_agent/agent.py`**

Read the file and add return types to the agent factory function.

- [ ] **Step 2: Annotate `src/websearch_agent/workflow.py`**

Read the file. LlamaIndex workflows use `@step` decorators. Add return types to unannotated workflow steps and helper functions.

- [ ] **Step 3: Annotate `src/websearch_agent/tracing.py`**

Same pattern. Add `-> None` to `enable_tracing` if missing.

- [ ] **Step 4: Annotate `main.py`**

Same FastAPI template pattern.

- [ ] **Step 5: Run ty check**

```bash
cd agents/llamaindex/templates/websearch_agent
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 6: Commit**

```bash
git add agents/llamaindex/templates/websearch_agent/
git commit -m "feat(llamaindex_websearch): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 9: Type annotations — autogen/mcp_agent

**Files:**
- Modify: `agents/autogen/templates/mcp_agent/src/autogen_agent_base/agent.py`
- Modify: `agents/autogen/templates/mcp_agent/src/autogen_agent_base/tracing.py`
- Modify: `agents/autogen/templates/mcp_agent/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent

- [ ] **Step 1: Annotate `src/autogen_agent_base/agent.py`**

Read the file and add return types. The agent factory likely returns an autogen agent type.

- [ ] **Step 2: Annotate `src/autogen_agent_base/tracing.py`**

Add `-> None` to `enable_tracing` and `check_mlflow_health` if missing.

- [ ] **Step 3: Annotate `main.py`**

Same FastAPI template pattern (7/15 already annotated — add the remaining 8).

- [ ] **Step 4: Run ty check**

```bash
cd agents/autogen/templates/mcp_agent
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/autogen/templates/mcp_agent/src/ agents/autogen/templates/mcp_agent/main.py
git commit -m "feat(autogen_mcp): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 10: Type annotations — autogen/mcp_automl_template

**Files:**
- Modify: `agents/autogen/templates/mcp_agent/mcp_automl_template/utils.py`
- Modify: `agents/autogen/templates/mcp_agent/mcp_automl_template/interact_with_mcp.py`
- Modify: `agents/autogen/templates/mcp_agent/mcp_automl_template/register_tools.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated template

- [ ] **Step 1: Annotate `utils.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 12 | `def dataframe_to_json_schema(df, ...) -> dict:` | Already annotated |
| 64 | `def dataframe_to_pydantic_model(df, ...) -> type[BaseModel]:` | Already annotated |
| 81 | `def json_schema_to_pydantic_model(schema, ...) -> type[BaseModel]:` | Already annotated |
| 135 | `def get_chat_from_env():` | `def get_chat_from_env() -> ChatOpenAI:` — add import `from langchain_openai import ChatOpenAI` at top |
| 165 | `def get_chat_llama_stack():` | `def get_chat_llama_stack() -> ChatLlamaStack:` — add import `from langchain_llama_stack import ChatLlamaStack` at top |

Note: Both `get_chat_*` functions do lazy imports. Move the import to the top of the file or use `TYPE_CHECKING` block:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI
    from langchain_llama_stack import ChatLlamaStack
```

- [ ] **Step 2: Annotate `interact_with_mcp.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 32 | `async def ask_question(agent, user_input: str):` | `async def ask_question(agent: Any, user_input: str) -> None:` |
| 41 | `async def chat_loop():` | `async def chat_loop() -> None:` |

Add `from typing import Any` import.

- [ ] **Step 3: Annotate `register_tools.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 19 | `def _resolve_schema_path(schema_path: str, config_dir: Path) -> Path:` | Already annotated |
| 27 | `def _coerce_null_in_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:` | Already annotated |
| 35 | `def _make_tool_handler_flat(...) -> Any:` | Already annotated |
| 110 | `def register_tools_from_config(mcp_server: Any, config_path: str \| Path) -> None:` | Already annotated |

Only the inner `handler` function (line 73) may need annotation: `def handler(**kwargs: Any) -> dict | str:` — verify it already has this.

- [ ] **Step 4: Run ty check**

```bash
cd agents/autogen/templates/mcp_agent/mcp_automl_template
uv sync --frozen
ty check --python .venv mcp_server.py register_tools.py utils.py interact_with_mcp.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/autogen/templates/mcp_agent/mcp_automl_template/
git commit -m "feat(automl_template): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 11: Type annotations — a2a/langgraph_crewai_agent

**Files:**
- Modify: `agents/a2a/templates/langgraph_crewai_agent/src/a2a_langgraph_crewai/a2a_reply.py`
- Modify: `agents/a2a/templates/langgraph_crewai_agent/src/a2a_langgraph_crewai/crew_a2a_server.py`
- Modify: `agents/a2a/templates/langgraph_crewai_agent/src/a2a_langgraph_crewai/langgraph_a2a_server.py`
- Modify: `agents/a2a/templates/langgraph_crewai_agent/src/a2a_langgraph_crewai/tracing.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent (this is the largest agent with ~24 functions in langgraph_a2a_server.py alone)

- [ ] **Step 1: Annotate `a2a_reply.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 32 | `def _unwrap_send_result(response: Any) -> Any:` | Already annotated |
| 39 | `def a2a_result_to_text(result: Message \| Task \| Any) -> str:` | Already annotated |
| 55 | `def _json_for_log(obj: Any) -> str:` | Already annotated |
| 66 | `async def send_a2a_text_message(base_url: str, text: str, timeout: float = 120.0) -> str:` | Already annotated |

All 4 functions are annotated. No changes needed.

- [ ] **Step 2: Annotate `crew_a2a_server.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 38 | `def _listen_port() -> int:` | Already annotated |
| 45 | `def _ensure_llm() -> LLM:` | Already annotated |
| 66 | `def _run_crew(user_prompt: str) -> str:` | Already annotated |
| 100 | `async def execute(self, context, event_queue) -> None:` | Already annotated |
| 120 | `async def cancel(self, context, event_queue) -> None:` | Already annotated |
| 124 | `def main() -> None:` | Already annotated |

All annotated. No changes needed.

- [ ] **Step 3: Annotate `langgraph_a2a_server.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 69 | `def _listen_port() -> int:` | Already annotated |
| 75 | `def _crew_base_url() -> str:` | Already annotated |
| 79 | `def _normalize_openai_base_url(base_url: str) -> str:` | Already annotated |
| 93 | `def _build_graph():` | `def _build_graph() -> Any:` (returns `create_agent(...)` which is a `CompiledGraph`) |
| 125 | `def _ensure_graph():` | `def _ensure_graph() -> Any:` |
| 132 | `def _single_ai_text(message: AIMessage) -> str:` | Already annotated |
| 146 | `def _last_ai_text(messages: list) -> str:` | Already annotated |
| 153 | `def _make_completion_id() -> str:` | Already annotated |
| 157 | `async def run_orchestrator(user_text: str) -> str:` | Already annotated |
| 165 | `def _jsonrpc_message_send_envelope(user_text: str) -> dict[str, Any]:` | Already annotated |
| 183 | `def _jsonrpc_ok_envelope(request_id: str, assistant_text: str) -> dict[str, Any]:` | Already annotated |
| 197 | `def _stream_chunk_text(raw: Any) -> str:` | Already annotated |
| 214 | `def _tool_call_to_delta(tc: Any, index: int) -> dict[str, Any]:` | Already annotated |
| 234 | `async def _stream_orchestrator_sse(...) -> AsyncIterator[str]:` | Already annotated |
| 361 | `async def execute(self, context, event_queue) -> None:` | Already annotated |
| 381 | `async def cancel(self, context, event_queue) -> None:` | Already annotated |
| 385 | `def _last_user_text(messages: list[dict[str, Any]]) -> str:` | Already annotated |
| 395 | `async def _playground_page(_request: Request) -> FileResponse:` | Already annotated |
| 401 | `async def _health(_request: Request) -> JSONResponse:` | Already annotated |
| 412 | `async def _serve_image(request: Request) -> FileResponse:` | Already annotated |
| 425 | `async def _chat_completions(request: Request) -> JSONResponse \| StreamingResponse:` | Already annotated |
| 470 | `def _build_starlette_app(agent_card: AgentCard, handler: DefaultRequestHandler) -> Starlette:` | Add `-> Starlette` |
| 486 | `def main() -> None:` | Already annotated |

Only `_build_graph`, `_ensure_graph`, and `_build_starlette_app` need annotations.

- [ ] **Step 4: Annotate `tracing.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 22 | `def sanitize_uri(uri: str) -> str:` | Already annotated |
| 45 | `def check_mlflow_health(...) -> None:` | Already annotated |
| 100 | `def wrap_func_with_mlflow_trace(...) -> Callable:` | Already annotated |
| 122 | `def enable_tracing_langgraph() -> None:` | Already annotated |
| 201 | `def enable_tracing_crewai() -> None:` | Already annotated |

All annotated. No changes needed.

- [ ] **Step 5: Run ty check**

```bash
cd agents/a2a/templates/langgraph_crewai_agent
uv sync --frozen
ty check --python .venv src/
```

- [ ] **Step 6: Commit**

```bash
git add agents/a2a/templates/langgraph_crewai_agent/
git commit -m "feat(a2a): add return type annotations to unannotated functions (RHAIENG-4064)"
```

---

### Task 12: Type annotations — vanilla_python/openai_responses_agent

**Files:**
- Modify: `agents/vanilla_python/templates/openai_responses_agent/src/openai_responses_agent/agent.py`
- Modify: `agents/vanilla_python/templates/openai_responses_agent/src/openai_responses_agent/tracing.py`
- Modify: `agents/vanilla_python/templates/openai_responses_agent/main.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated agent (largest `agent.py` with 15 functions)

- [ ] **Step 1: Annotate `src/openai_responses_agent/agent.py`**

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 27 | `def get_agent_closure(...) -> Callable:` | Already annotated |
| 42 | `def get_agent() -> "_AIAgentAdapter":` | Already annotated |
| 78 | `async def run(self, input: ...) -> Dict[str, Any]:` | Already annotated |
| 107 | `def _messages_to_responses_input(messages: List[Dict]) -> tuple[str, List[Dict]]:` | Already annotated |
| 130 | `def _get_output_text_from_response(response: Any) -> str:` | Already annotated |
| 189 | `def add_message(self, role: str, content: str) -> None:` | Already annotated |
| 193 | `def register_tool(self, name: str, func: Callable) -> None:` | Already annotated |
| 197 | `def _function_to_string(self, func: Callable) -> str:` | Already annotated |
| 201 | `def _parse_arguments(self, args_str: str) -> List[str]:` | Already annotated |
| 207 | `def _responses_create(self, ...):` | `def _responses_create(self, ...) -> Any:` |
| 239 | `def _execute(self) -> str:` | Already annotated |
| 248 | `def query(self, ...) -> Optional[str]:` | Already annotated |
| 313 | `def setup_system_prompt(self) -> None:` | Already annotated |

Only `_responses_create` needs a return type. Add `-> Any` (the return type is `openai.types.responses.Response` but `Any` is sufficient).

- [ ] **Step 2: Annotate `src/openai_responses_agent/tracing.py`**

Add return types to:
- `check_mlflow_health` → `-> None`
- `enable_tracing` → `-> None`
- `wrap_func_with_mlflow_trace` → `-> Callable` (check if already present)

- [ ] **Step 3: Annotate `main.py`**

Same FastAPI template pattern. This agent has 15 functions in main.py with only 2 annotated. Add return types to all 13 remaining.

- [ ] **Step 4: Run ty check**

```bash
cd agents/vanilla_python/templates/openai_responses_agent
uv sync --frozen
ty check --python .venv src/ main.py
```

- [ ] **Step 5: Commit**

```bash
git add agents/vanilla_python/templates/openai_responses_agent/
git commit -m "feat(openai_responses): add return type annotations to all functions (RHAIENG-4064)"
```

---

### Task 13: Type annotations — components/auth

**Files:**
- Modify: `components/auth/src/agent_auth/middleware.py`

**Interfaces:**
- Consumes: None (standalone)
- Produces: Fully annotated middleware component

- [ ] **Step 1: Annotate `middleware.py`**

Most functions already have return types (8/10). Check which 2 are missing:

| Line | Current signature | Annotated signature |
|------|-------------------|---------------------|
| 132 | `async def _send_json(` | Check and add `-> None` |

Read the file and identify the remaining unannotated functions. Add `-> None` or the appropriate type.

- [ ] **Step 2: Run ty check**

```bash
cd components/auth
uv sync --frozen
ty check --python .venv src/
```

- [ ] **Step 3: Commit**

```bash
git add components/auth/
git commit -m "feat(auth): add return type annotations to remaining functions (RHAIENG-4064)"
```

---

### Task 14: Final verification — full type-check pass

**Files:**
- No file changes (verification only)

**Interfaces:**
- Consumes: All changes from Tasks 1–13
- Produces: Confirmation that all agents pass ty with zero `--ignore` flags

- [ ] **Step 1: Run ty check on every agent**

```bash
for dir in \
  agents/langgraph/templates/react_agent \
  agents/langgraph/templates/agentic_rag \
  agents/langgraph/templates/human_in_the_loop \
  agents/langgraph/templates/react_with_database_memory \
  agents/google/templates/adk \
  agents/crewai/templates/websearch_agent \
  agents/llamaindex/templates/websearch_agent \
  agents/autogen/templates/mcp_agent \
  agents/a2a/templates/langgraph_crewai_agent \
  agents/vanilla_python/templates/openai_responses_agent \
  components/auth; do
  echo "=== Checking $dir ==="
  (cd "$dir" && uv sync --frozen && ty check --python .venv src/ $([ -f main.py ] && echo main.py)) || echo "FAILED: $dir"
done
```

```bash
echo "=== Checking autogen-automl ==="
cd agents/autogen/templates/mcp_agent/mcp_automl_template
uv sync --frozen
ty check --python .venv mcp_server.py register_tools.py utils.py interact_with_mcp.py
```

Expected: All agents pass with no errors.

- [ ] **Step 2: Run annotation coverage report**

```bash
python3 -c "
import re, subprocess
result = subprocess.run(['find', 'agents', 'components', '-name', '*.py', '-path', '*/templates/*', '-o', '-name', '*.py', '-path', '*/src/*'], capture_output=True, text=True)
files = [f for f in result.stdout.strip().split('\n') if f and '__pycache__' not in f and '/tests/' not in f]
total = annotated = 0
for f in sorted(set(files)):
    with open(f) as fh:
        for line in fh:
            if re.search(r'^\s*(?:async\s+)?def\s+', line):
                total += 1
                if '->' in line:
                    annotated += 1
print(f'Total functions: {total}')
print(f'Annotated: {annotated}')
print(f'Coverage: {annotated/total*100:.1f}%')
assert annotated/total >= 0.80, f'Coverage {annotated/total*100:.1f}% < 80% target'
print('PASS: Coverage target met')
"
```

Expected: Coverage ≥ 80% (target: 100%)

- [ ] **Step 3: Run existing tests to verify no regressions**

```bash
for dir in \
  agents/langgraph/templates/react_agent \
  agents/langgraph/templates/agentic_rag \
  agents/langgraph/templates/human_in_the_loop \
  agents/langgraph/templates/react_with_database_memory \
  agents/google/templates/adk \
  agents/crewai/templates/websearch_agent \
  agents/llamaindex/templates/websearch_agent \
  agents/autogen/templates/mcp_agent \
  agents/vanilla_python/templates/openai_responses_agent; do
  echo "=== Testing $dir ==="
  (cd "$dir" && make test) || echo "FAILED: $dir"
done
```

Expected: All tests pass. Type annotation changes should not affect runtime behavior.
