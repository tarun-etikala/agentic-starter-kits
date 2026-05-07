# RHAISTRAT-1376: Agent Template & Demo Discovery via Dashboard Learning Resources

## Context

AI Engineers using RHOAI have no centralized way to discover agent templates and demos. Templates are scattered across GitHub repos with no in-product catalog. This feature adds **OdhApplication** and **OdhDocument** Kustomize manifests to the [odh-dashboard](https://github.com/opendatahub-io/odh-dashboard) so that agent templates appear on the Explore page with linked tutorials in the Resources section.

**PR #6299** (open, not merged) in `opendatahub-io/odh-dashboard` is the implementation vehicle. Changes are needed there, not in this `agentic-starter-kits` repo.

---

## Acceptance Criteria vs Current PR State

| # | Acceptance Criterion | PR Status | Gap? |
|---|---------------------|-----------|------|
| 1 | Agentic Starter Kits as OdhApplication with tutorials (LangGraph ReAct, LlamaIndex Workflow, LlamaStack, Agentic RAG) | **Partial** — OdhApplication exists with **11** tutorials (exceeds AC scope) | AC lists "LlamaStack" tutorial but PR has "Vanilla Python / OpenAI Responses" instead (correctly renamed per CodeRabbit review). **AC is stale — needs updating to reflect the actual 11 agents.** |
| 2 | Llama Stack Demos as OdhApplication with progressive tutorials (RAG, tool calling, multi-agent, knowledge assistant, evaluation) | **Missing** — Removed in commit `be1b01ee` ("will be added in a separate PR") | **Major gap.** The AC requires this but it was deliberately descoped from the PR. Needs a decision: update the AC to remove this, or create a follow-up Jira. |
| 3 | Resources discoverable via **"Agent Templates"** category filter on the Explore page | **Mismatch** — PR uses `'AI agents,Getting started,Model development'` | The category annotation is `"AI agents"`, not `"Agent Templates"` as the AC states. Categories in odh-dashboard are free-form annotation strings — the Explore page renders whatever values exist. **Need to align on the canonical name.** |
| 4 | Each resource links directly to corresponding GitHub repo/tutorial | **Done** | All 11 tutorial URLs point to correct paths under `red-hat-data-services/agentic-starter-kits`. |
| 5 | Wired into `manifests/common/apps/kustomization.yaml` | **Done** (for agentic-starter-kits only) | Llama Stack Demos not wired since they were removed. |
| 6 | App cards on Explore page, tutorials in Resources section | **Likely works** but needs cluster verification | CI passes (the one Cypress failure is an unrelated `projects/tabs` test). |

---

## Detailed Gaps & Refinement Suggestions

### Gap 1: Llama Stack Demos — Descoped but still in AC

**What happened:** The initial PR included both Agentic Starter Kits and Llama Stack Demos. Llama Stack Demos were removed in a later commit with the message "will be added in a separate PR once the repo stabilizes further."

**Refinement options:**

- **Option A (recommended):** Update the Jira AC to remove Llama Stack Demos from this ticket. Create a new child/follow-up Jira (e.g., "Llama Stack Demos dashboard resources") and link it. This keeps RHAISTRAT-1376 shippable.
- **Option B:** Re-add Llama Stack Demos to PR #6299 if the upstream repo has stabilized. The prior commits show the manifests existed and worked.

### Gap 2: Category Name — "Agent Templates" vs "AI agents"

**AC says:** `"Agent Templates"` category filter
**PR uses:** `opendatahub.io/categories: 'AI agents,Getting started,Model development'`

The dashboard dynamically builds sidebar filters from whatever category strings exist in `opendatahub.io/categories` annotations. There is no hardcoded "Agent Templates" category.

**Refinement:**

- If the product/UX team wants the filter to say "Agent Templates", change the annotation to `'Agent Templates,Getting started'`.
- If "AI agents" is the preferred label (more generic, covers both templates and demos), update the AC to say "AI agents".
- **Recommendation:** Align with PM/UX on the exact label. "AI agents" is broader and better for discoverability if more agent-related resources are added later.

### Gap 3: AC Tutorial List is Stale

**AC lists 4 tutorials:** LangGraph ReAct, LlamaIndex Workflow, LlamaStack, Agentic RAG
**PR includes 11 tutorials:**

| Tutorial | Framework | In AC? |
|----------|-----------|--------|
| LangGraph ReAct Agent | langgraph | Yes |
| LlamaIndex Workflow Agent | llamaindex | Yes |
| Agentic RAG | langgraph | Yes |
| Vanilla Python / OpenAI Responses | vanilla_python | No (was "LlamaStack" in AC) |
| CrewAI WebSearch Agent | crewai | No |
| AutoGen MCP Agent | autogen | No |
| Langflow Tool-Calling Agent | langflow | No |
| LangGraph ReAct + DB Memory | langgraph | No |
| A2A LangGraph + CrewAI | a2a | No |
| Google ADK 2.0 Agent | google | No |
| LangGraph Human-in-the-Loop | langgraph | No |

**Refinement:** Update the AC to list all 11 tutorials. The repo has grown since the ticket was written. All 11 are valid and match actual agents in the `agentic-starter-kits` repo.

### Gap 4: GitHub URL Target — Downstream vs Upstream

All tutorial URLs point to `https://github.com/red-hat-data-services/agentic-starter-kits/...` (the downstream/Red Hat fork), not `opendatahub-io/...`.

**Assessment:** This is likely **correct** for RHOAI (the product ships from `red-hat-data-services`). However, verify this is the intended public-facing URL — if the repo is private or moves, links will break.

### Gap 5: API Contract Wording in App Description

The `getStartedMarkDown` in the OdhApplication says:
> Each agent exposes a FastAPI server with `/chat` and `/health` endpoints.

But per `AGENTS.md`, the actual endpoints are `POST /chat/completions` and `GET /health`.

**Refinement:** Fix the description to say `/chat/completions` instead of `/chat`.

### Gap 6: CI Status

- One Cypress test failure (`projects/tabs`) appears **unrelated** to this PR — it's a pre-existing flake.
- The `Red Hat Konflux` pipeline also fails — needs investigation to determine if it's blocking.

---

## Recommended Actions

### On Jira (RHAISTRAT-1376)

1. **Update AC #1** to list all 11 current tutorials instead of only 4
2. **Update AC #2** to either remove Llama Stack Demos (defer to follow-up Jira) or keep as a separate deliverable
3. **Update AC #3** to clarify the category name — confirm "AI agents" vs "Agent Templates" with PM/UX
4. Add "Vanilla Python / OpenAI Responses" to replace "LlamaStack" in the tutorial list (the rename was correct)

### On PR #6299 (odh-dashboard)

1. Fix `getStartedMarkDown` endpoint reference: `/chat` → `/chat/completions`
2. Confirm category annotation name with PM/UX and update if needed
3. Investigate Konflux pipeline failure
4. Get maintainer review and merge

### Follow-up Work

1. Create a new Jira for "Llama Stack Demos Dashboard Resources" if AC #2 is descoped
2. Verify `red-hat-data-services/agentic-starter-kits` repo visibility (public vs private) since all tutorial URLs depend on it
3. After merge, deploy to a dev cluster and verify: app card on Explore page, tutorials in Resources, category filter works

---

## Verification Plan

1. `kustomize build manifests/overlays/dev` succeeds in the odh-dashboard repo
2. Apply resources to a dev cluster
3. Confirm "Agentic Starter Kits" card appears on the Explore page
4. Confirm all 11 tutorial documents appear in the Resources section
5. Confirm the category filter (whichever name is chosen) appears and filters correctly
6. Click each tutorial URL and verify it resolves to the correct GitHub page
