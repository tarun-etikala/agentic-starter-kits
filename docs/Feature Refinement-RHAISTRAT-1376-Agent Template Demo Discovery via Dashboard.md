| Feature Refinement - RHAISTRAT-1376 - Agent Template & Demo Discovery via Dashboard Learning Resources |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| ----- | :---- | ----- | ----- | ----- | ----- | :---- | ----- | ----- | ----- | ----- | :---- | ----- | ----- | ----- | ----- |
| Feature Jira Link | [RHAISTRAT-1376](https://redhat.atlassian.net/browse/RHAISTRAT-1376) |  |  |  |  | Status |  |  |  |  | Refinement |  |  |  |  |
| Slack Channel / Thread | TBD |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Feature Owner | <nommen@redhat.com> |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Delivery Owner | TBD |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| RFE Council Reviewer | TBD |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Product | RHOAI |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## Feature Details

### Feature Overview

AI Engineers using RHOAI have no centralized, in-product place to discover agent templates and demos. Templates are scattered across GitHub repositories (`red-hat-data-services/agentic-starter-kits`) with no guided catalog, forcing discovery through word-of-mouth or manual GitHub browsing.

This feature adds **OdhDocument** Kustomize manifest resources to the [odh-dashboard](https://github.com/opendatahub-io/odh-dashboard) so that:

- Each agent template appears as an **individual card in the Learning Resources** section — one card per agent, not a single umbrella application.
- Resources are filterable by an **"Agent Templates"** category in the sidebar.
- Each card links directly to the corresponding GitHub repository README for that specific agent.

> **Note:** This feature does **not** create an OdhApplication on the Explore page. Agent templates are not standalone applications — they are learning resources. The OdhDocument CRD supports independent category annotations without requiring an OdhApplication parent.

**Personas who benefit:**

- **AI Engineer (Alex):** Can browse individual agent template cards directly from the RHOAI dashboard Learning Resources section, filtered by "Agent Templates" category, and pick the right pattern for their use case — from simple ReAct agents to multi-agent A2A patterns.
- **Platform/Ops Engineer (Paula):** Can publish curated agent templates as dashboard learning resources so that AI Engineers discover validated scaffolds through the standard product surface.

**Current state vs. target state:**

| Today | With this feature |
|-------|-------------------|
| Agent templates live only on GitHub | Each agent template discoverable as an individual card in the RHOAI dashboard Learning Resources section |
| No categorization or learning path | Agent cards organized under "Agent Templates" category filter with clear descriptions |
| No in-product link from "I want to build an agent" to a starting point | Each agent card links directly to its specific GitHub README |

### PM Decisions (Resolved during refinement — 2026-04-20/21)

| # | Question | Decision |
|---|----------|----------|
| 1 | Should this be visible in both ODH and RHOAI? | RHOAI is the main goal. ODH visibility is not in scope for this feature. |
| 2 | Badge: "Self-managed" or custom badge? | Not applicable — no OdhApplication app card is being created. Agent templates appear as OdhDocument learning resources only. |
| 3 | Is this Red Hat certified and supported? | **No.** This is community/experimental. Not certified or supported. |
| 4 | Attribution: "by Red Hat" or "by Open Data Hub"? | **"by Red Hat"** — the repo is under `red-hat-data-services`. Must clearly indicate it is not supported. |
| 5 | Is there an approved icon/logo? | **No.** No approved logo. Keep it as simple as possible. |
| 6 | Feature flag? | **No.** Feature flags are for supported DP/TP components. This follows the standard Learning Resources page logic — no gating. |
| 7 | Llama Stack demos: separate card or grouped? | **Out of scope.** This feature is scoped to agentic-starter-kits discoverability only. Llama Stack demos are a separate effort. |
| 8 | One umbrella card or separate per agent? | **Separate card per agent.** Team agreed that for a user asking "I want to build X with Y", individual agent cards are better. |
| 9 | Learning Resources vs Explore page? | **Learning Resources only.** Agent templates are not standalone applications. The Explore page is for apps like Starburst. |

### The Why

**Summit 3.4 alignment:** Agentic AI is a headline theme for Summit 3.4. Customers and partners expect to see agent capabilities surfaced in the product, not buried in GitHub. Discoverable templates in the dashboard demonstrate platform maturity and give field teams and SAs a concrete asset to show during demos and POCs.

**Customer and partner evidence:**

- The Kagenti initiative (RHAISTRAT-1290, same assignee) is building agent deployment/runtime infrastructure for OpenShift AI. That feature assumes developers *already know which template to start from*. Without in-product discovery, the Kagenti onboarding story has a gap at the very first step: "find a starting point."
- Field teams and SAs currently answer "how do I build an agent on RHOAI?" by sending GitHub links over Slack or email. There is no self-service path. This mirrors the pattern seen in RHAISTRAT-1473 (tool calling config), where validated information existed but was scattered across docs, issues, and tribal knowledge -- leading to support escalations that a single in-product surface would have prevented.
- Partner frameworks (LangGraph, LlamaIndex, CrewAI, Google ADK) each have their own getting-started docs. Without a unified catalog, customers must evaluate frameworks one-by-one across different sites. A centralized dashboard surface makes RHOAI the single entry point.

**Competitive positioning:** Competing platforms (AWS Bedrock Agent Blueprints, Azure AI Agent Service templates) provide in-console template catalogs. RHOAI users currently get no equivalent -- the gap is visible in competitive evaluations.

**Ecosystem growth:** The `agentic-starter-kits` repo has grown from 4 agents to 11 across 8 frameworks in under two months. Without a discovery surface, each new template added is invisible to users who don't watch the GitHub repo. A dashboard catalog ensures every template gets equal visibility automatically.

**Alternatives considered:**

- *OdhQuickStart (interactive walkthrough) instead of OdhDocument (tutorial link):* QuickStarts provide a richer in-product experience but require significantly more content authoring per agent. OdhDocument tutorials with GitHub links are the right starting point; QuickStarts can be added incrementally as a follow-up.
- *Embed documentation in-product instead of linking to GitHub:* Would solve the disconnected-environment gap but creates a maintenance burden (content goes stale). Linking to the repo README -- which is maintained alongside the code -- keeps docs and code in sync.
- *Add agents to the Model Catalog instead of the Learning Resources page:* Agents are not models. The Model Catalog is for model serving. Mixing these would confuse both UX patterns.
- *Create an OdhApplication on the Explore page:* PM decided agent templates are not standalone applications (like Starburst). Learning Resources with individual agent cards better serves the "I want to build X with Y" use case.

**Cost:** Zero runtime cost. This feature is purely Kustomize manifests (OdhDocument YAMLs) using the existing dashboard CRD pipeline. No new pods, operators, or APIs.

### High Level Requirements

1. **As an AI Engineer**, I want to see individual agent template cards in the RHOAI Learning Resources section — one for each agent (LangGraph ReAct, LlamaIndex Workflow, CrewAI WebSearch, AutoGen MCP, Langflow Tool-Calling, Vanilla Python OpenAI Responses, LangGraph Agentic RAG, LangGraph Memory, LangGraph Human-in-the-Loop, Google ADK, A2A LangGraph+CrewAI) — so that I can pick the right pattern for my use case.
2. **As an AI Engineer**, I want to filter resources by an "Agent Templates" category, so that I can quickly narrow down to agent-related content.
3. **As an AI Engineer**, I want each agent card to link directly to its specific GitHub README, so that I can follow step-by-step instructions immediately.
4. **As an AI Engineer**, I want each card to clearly indicate this is community content by Red Hat (not supported), so that I understand the support level.
5. **As a Platform Engineer**, I want these resources deployed automatically via Kustomize manifests, so that they appear on any RHOAI instance without manual intervention.

### Non-Functional Requirements

- **No runtime dependencies:** This feature is purely Kustomize manifests (OdhDocument YAMLs). No new pods, services, or operators are introduced.
- **Performance:** Zero impact -- manifests are applied at install/upgrade time and rendered by the existing dashboard frontend.
- **Security:** No new attack surface. Tutorial URLs are static links to public GitHub repositories. No secrets, no API calls.
- **Disconnected environments:** Tutorial URLs point to external GitHub repos. In air-gapped/disconnected clusters, the cards will appear in Learning Resources but links will not resolve. Consider adding a note in the card description about internet connectivity requirement.
- **Upgrade considerations:** New OdhDocument resources are purely additive. No migration or breaking changes to existing resources.
- **Accessibility:** Uses standard PatternFly components (cards) via the existing dashboard Learning Resources UI. No custom UI work needed.

### Out-of-Scope

- **Llama Stack Demos:** Out of scope. This feature is scoped to agentic-starter-kits discoverability only. Llama Stack demos are a separate effort if needed.
- **Explore page app card:** No OdhApplication is created. Agent templates are not standalone applications — they are learning resources only.
- **In-product agent deployment:** This feature provides discovery only (links to GitHub). One-click deploy-from-dashboard is a separate initiative.
- **Custom dashboard UI changes:** No new frontend components, pages, or routes. Uses existing OdhDocument Learning Resources rendering.
- **Notebook/workbench integration:** No auto-import of agent code into JupyterLab workbenches.
- **Offline/bundled documentation:** Tutorial content is not bundled; requires internet access to reach GitHub.
- **ODH visibility:** Scoped to RHOAI only for initial delivery.

### Acceptance Criteria

1. **Given** the RHOAI dashboard is deployed with the new manifests, **When** a user navigates to the Learning Resources page, **Then** 11 individual agent template cards appear, one for each agent: LangGraph ReAct, LlamaIndex Workflow, Vanilla Python OpenAI Responses, Agentic RAG, CrewAI WebSearch, AutoGen MCP, Langflow Tool-Calling, LangGraph Memory, A2A LangGraph+CrewAI, Google ADK, LangGraph Human-in-the-Loop.

2. **Given** the user is on the Learning Resources page, **When** they select the "Agent Templates" category filter in the sidebar, **Then** only the 11 agent template cards are shown.

3. **Given** the user clicks any agent template card, **When** the link opens, **Then** it navigates to the correct GitHub repository path under `red-hat-data-services/agentic-starter-kits/tree/main/agents/<framework>/<agent_name>`.

4. **Given** any agent template card, **When** displayed, **Then** the provider shows "Red Hat" and the description clearly indicates this is community content (not supported).

5. **Given** a cluster admin runs `kustomize build manifests/overlays/dev`, **When** the build completes, **Then** the output includes all 11 OdhDocument resources with `opendatahub.io/categories: 'Agent Templates'` annotations. No OdhApplication resource is created.

6. **Given** the Explore page, **When** a user browses it, **Then** no "Agentic Starter Kits" app card appears — agent templates are surfaced only through Learning Resources.

7. **Measured by:** (future telemetry) Dashboard analytics tracking click-through rates on individual agent template cards in Learning Resources.

### Risks & Assumptions

**Risks:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| `red-hat-data-services/agentic-starter-kits` repo is private or visibility changes | All 11 tutorial URLs break for external users | Verify repo is public before merge; add monitoring for link rot |
| Upstream repo restructures agent directory paths | Tutorial URLs return 404 | Pin URLs to a stable branch/tag, or add a redirect mechanism |
| "Agent Templates" category has only 11 cards from one repo | Users may expect broader content under this filter | Plan to add future agent resources (e.g., Llama Stack demos) under the same category |
| Disconnected/air-gapped clusters cannot reach GitHub | Tutorial links non-functional | Document this limitation; future work could bundle docs |
| PR #6299 needs rework to remove OdhApplication and use OdhDocument-only approach | Additional development time | Scope is smaller (remove code rather than add); manifests are straightforward |

**Assumptions:**

| Assumption | Validation needed |
|------------|------------------|
| The `red-hat-data-services/agentic-starter-kits` GitHub repo will remain public and at the current URL structure | Confirm with repo owners |
| The 11 agents currently in the repo represent the final set for initial release | Confirm no additional agents are planned before merge |
| "Agent Templates" is the approved category label | Confirmed by PM (matches original Jira AC) |
| OdhDocument `type: tutorial` is the correct document type for these resources | Confirmed -- matches dashboard convention |
| OdhDocuments can appear in Learning Resources without an OdhApplication parent | Confirmed -- `appName` is optional in the CRD; categories are annotation-based and independent |
| No OdhQuickStart (interactive walkthrough) is needed for initial release | Confirmed -- could be a follow-up |
| Provider field set to "Red Hat" with community/unsupported disclaimer in description | PM confirmed "by Red Hat" with clear unsupported messaging |

### Architecture Review Check

Does the feature have the label "requires_architecture_review"? **NO**

Does the related RFE indicate "Requires architecture review: YES"? **NO**

**Rationale:** This feature is purely additive Kustomize manifests (OdhDocument CRDs) using existing dashboard infrastructure. No new components, APIs, operators, or runtime services are introduced. No cross-component architectural decisions are needed.

### Supporting Documentation

| Document | Link |
|----------|------|
| Jira Feature | [RHAISTRAT-1376](https://redhat.atlassian.net/browse/RHAISTRAT-1376) |
| Implementation PR | [opendatahub-io/odh-dashboard#6299](https://github.com/opendatahub-io/odh-dashboard/pull/6299) |
| Source repo (agents) | [red-hat-data-services/agentic-starter-kits](https://github.com/red-hat-data-services/agentic-starter-kits) |
| Related Jiras | RHAIRFE-1172 (LangChain/LangGraph), RHAIRFE-1174 (LlamaIndex), RHAISTRAT-1192 (Langflow), RHAIRFE-1307 (CrewAI), RHAIRFE-1026 (Llama Stack) |
| Dashboard OdhDocument pattern | `manifests/common/apps/jupyter/jupyter-docs.yaml` (reference implementation) |
| Dashboard category filtering | `frontend/src/pages/learningCenter/CategoryFilters.tsx` (dynamically built from annotations) |

---

## New Feature / Component Prerequisites & Dependencies

### ODH/RHOAI build process Onboarding

**Not required.** This feature adds only Kustomize manifest files (YAML) to the existing `odh-dashboard` repository. No new component, operator, or container image is being onboarded into the platform operator. The manifests are deployed through the existing dashboard Kustomize pipeline.

### Licence Validation

Will this feature require bringing in new upstream projects or sub-projects into the product? **NO**

This feature adds static YAML manifests only. The `agentic-starter-kits` repo itself is Apache 2.0 licensed. No new upstream dependencies are pulled into the dashboard build.

### Accelerator/Package Support

Does this feature require support from the AIPCC team? **NO**

No new wheels, RPMs, or accelerator-specific content. Purely manifest-based.

### Documentation Support

Does this feature require support from the documentation team? **YES**

- The Learning Resources section should mention the new agent template cards in the RHOAI product documentation.
- Release Notes should flag this as a new feature for Summit 3.4.
- Consider adding a "Building AI Agents" topic to the product docs that references these tutorials.
- Documentation should note that these are community resources by Red Hat (not supported).

### UXD Support

Does this feature require support from the UXD team? **NO** (for initial release)

The feature uses existing OdhDocument Learning Resources rendering. No custom UI components. No icon needed (no app card). PM confirmed "Agent Templates" as the category label and no approved logo exists — keep it simple.

### Performance Team Support

Does this feature require support from the performance (PSAP) team? **NO**

Zero runtime impact -- static manifests only.

### Add'l dependencies

- **odh-dashboard maintainer review:** PR #6299 needs review and approval from the dashboard team.
- **GitHub repo visibility:** The `red-hat-data-services/agentic-starter-kits` repo must be publicly accessible for tutorial URLs to work.

---

## High Level Plan

| Team | Start Date | Work (EPIC) | Dependencies | T-Shirt Size | Approval/Comments |
|------|-----------|-------------|--------------|-------------|-------------------|
| Agentic Starter Kits team | In progress | Maintain source agents repo, ensure README quality for all 11 agents; rework PR #6299 to remove OdhApplication and use OdhDocument-only approach | None | S | PR #6299 needs rework per PM decisions |
| Dashboard Team (Contact: Eder Ignatowicz) | After PR rework | Review and merge updated PR #6299 into odh-dashboard | PR review, CI green | S | Awaiting reworked PR |
| team-ai-core-platform | N/A | No platform operator changes needed | None | - | N/A for this feature |
| Product Security (Contact: Owen Watkins) | N/A | No security review needed (static manifests, no new APIs) | None | - | N/A |

---

## Gap Analysis & Recommendations

### Gaps Found Between Jira AC and PR #6299

| # | Gap | Severity | Status | Resolution |
|---|-----|----------|--------|------------|
| 1 | **Llama Stack Demos removed** from PR but still in Jira AC #2 | High | **Resolved** | PM confirmed out of scope. Scoped to agentic-starter-kits only. Remove from Jira AC. |
| 2 | **Category name mismatch**: PR originally used "AI agents" | Medium | **Resolved** | PM confirmed "Agent Templates" as the category label. Update PR accordingly. |
| 3 | **AC tutorial list is stale**: lists 4 tutorials, PR has 11 | Medium | **Resolved** | AC updated in this doc to list all 11 agents. Update Jira AC to match. |
| 4 | **Endpoint typo in app description**: says `/chat` instead of `/chat/completions` | Low | **Open** | Fix in PR #6299 (if app description is retained in any form). |
| 5 | **Disconnected environment support** not addressed | Low | **Open** | Add a note in card descriptions. Future: bundle docs for air-gapped. |
| 6 | **No telemetry events** defined for measuring adoption | Low | **Open** | Add Segment tracking for card clicks (uses existing `fireMiscTrackingEvent`). |
| 7 | **OdhApplication on Explore page** not wanted by PM | High | **Resolved** | PM decided agent templates are not standalone apps. Remove OdhApplication from PR. Use OdhDocument-only approach in Learning Resources. |
| 8 | **Support level and attribution** not specified | Medium | **Resolved** | Community (not supported), "by Red Hat". No badge needed (no app card). |

### Architectural Recommendations for odh-dashboard Changes

**1. OdhDocument-only approach — no OdhApplication needed.** The OdhDocument CRD's `appName` field is optional. OdhDocuments appear in Learning Resources independently, with category filtering driven by `opendatahub.io/categories` annotations on each document. The Learning Center page (`LearningCenter.tsx`) renders OdhDocument cards with category filtering via `CategoryFilters.tsx`. Adding `"Agent Templates"` in each document's annotation automatically creates the sidebar filter.

**2. PR #6299 rework required.** Remove the OdhApplication resource. Keep the 11 OdhDocuments, ensuring each has its own `opendatahub.io/categories: 'Agent Templates'` annotation (not inherited from an app). Set `provider: "Red Hat"` on each document. Add community/unsupported disclaimer in descriptions.

**3. Consider OdhQuickStart for a future iteration.** The jupyter app uses `OdhQuickStart` resources for interactive step-by-step walkthroughs (see `create-jupyter-notebook-quickstart.yaml`). A future enhancement could add a QuickStart for "Deploy your first agent on OpenShift" that walks users through `make build && make deploy`.

**4. Manifest structure follows established convention.** The PR should follow the `manifests/common/apps/<app-name>/` directory pattern with a local `kustomization.yaml` wiring individual OdhDocument resources.

**5. Two non-standard agents need callouts.** The Langflow and A2A tutorials link to agents that have non-standard deployment patterns (Podman Compose and `python:3.12-slim` respectively, per `AGENTS.md`). Their tutorial descriptions should clearly note these differences so users aren't confused when the deployment steps differ from other agents.
