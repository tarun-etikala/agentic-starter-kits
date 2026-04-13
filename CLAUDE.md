@AGENTS.md

## Claude Code

### Workflow
- Use plan mode for multi-file changes or unfamiliar areas of the codebase
- When modifying an agent, `cd` into its directory first — Makefiles use relative paths
- Use subagents for cross-agent investigations to keep main context clean
- Reference `agent.yaml` to discover required env vars before editing `.env.example`
- Prefer `make test` over running pytest directly to ensure correct env setup
- After editing Dockerfiles, verify the build with `make build` when possible
- If an agent has no tests, note it to the user — don't fabricate a passing result

### Boundaries
- Don't modify `charts/agent/` templates unless the change is explicitly requested
- Don't modify CONTRIBUTING.md, CI config, or root Makefile without asking
- When working on one agent, don't refactor other agents
- Don't change the API contract (`POST /chat/completions`, `GET /health`) without discussion
- When unsure if an agent follows the standard pattern, check its Makefile and Dockerfile first
