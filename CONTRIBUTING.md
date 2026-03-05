# Contributing to Agentic Starter Kits

Thank you for your interest in contributing. This document gives a short overview of how to get involved.

## How to contribute

- **Report bugs or suggest features** – Open an [issue](https://github.com/red-hat-data-services/agentic-starter-kits/issues) and describe the problem or idea. Check existing issues first to avoid duplicates.

- **Submit code changes** – Create a branch (in your fork or directly in this repo if you have access), make your changes, and open a pull request (PR). You don’t need to fork if you can push branches here. Keep PRs focused; one feature or fix per PR is easier to review.

- **Improve documentation** – Fixes and clarifications in the README, agent docs, or code comments are always welcome. Use the `docs:` prefix in your commit (see below).

- **Add or fix tests** – If you add or change behavior, consider adding or updating tests and use the `test:` prefix in commits.

Before submitting, please read our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Adding a new agent

The repository is organized by framework under `agents/`. To add a new agent:

1. **Create your agent directory** — Use an existing agent as a reference:
   ```bash
   cp -r agents/langgraph/react_agent agents/<framework>/<agent_name>
   ```
   Replace `<framework>` with the framework name (e.g. `langgraph`, `llamaindex`, `crewai`) and `<agent_name>` with a descriptive name.

2. **Implement your agent** — Add your source code under `src/<package_name>/`. At minimum you need:
   - `agent.py` — Agent logic
   - `tools.py` — Tool definitions (if any)

3. **Configure metadata** — Update `agent.yaml` with:
   - Agent name, description, framework
   - Required/optional environment variables
   - Resource requests/limits

4. **Configure Helm values** — Update `values.yaml` with any agent-specific overrides (extra env vars, volumes, resources).

5. **Add a template.env** — List all environment variables your agent needs (commented out as a template).

6. **Test locally** — Ensure your agent runs:
   ```bash
   cd agents/<framework>/<agent_name>
   cp template.env .env
   # Fill in .env values
   uv pip install .
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```

7. **Test deployment** — Build and deploy with agentctl:
   ```bash
   docker build -t <registry>/<agent>:latest .
   docker push <registry>/<agent>:latest
   ./scripts/agentctl deploy <registry>/<agent>:latest -a <framework>/<agent_name>
   ```

### Directory structure for a new agent

```
agents/<framework>/<agent_name>/
├── agent.yaml         # Agent metadata
├── values.yaml        # Helm values override
├── template.env       # Environment variable template
├── Dockerfile         # Container build
├── main.py            # FastAPI entrypoint
├── pyproject.toml     # Python dependencies
├── README.md          # Agent documentation
├── src/<package>/     # Source code
│   ├── __init__.py
│   ├── agent.py
│   └── tools.py
├── tests/             # Tests
└── examples/          # Usage examples
```

## Deploying with agentctl

The `scripts/agentctl` CLI replaces the old per-agent `deploy.sh` scripts. It uses Helm charts for consistent, repeatable deployments.

```bash
# Deploy an agent
./scripts/agentctl deploy <image> --namespace <ns> --agent <framework>/<agent>

# List deployed agents
./scripts/agentctl list

# Check status
./scripts/agentctl status <release-name> --namespace <ns>

# Remove an agent
./scripts/agentctl destroy <release-name> --namespace <ns>
```

## Commit message conventions

We encourage [Conventional Commits](https://www.conventionalcommits.org/) so that history and release notes stay clear.

Use one of these prefixes at the start of your commit message:

| Prefix    | Meaning |
| --------- | -------- |
| **feat:** | A new feature |
| **fix:**  | A bug fix |
| **perf:** | A change that improves performance |
| **chore:**| Maintenance (deps, tooling, config) |
| **docs:** | Documentation only |
| **test:** | Adding or updating tests |

You can optionally add a scope (e.g. the agent or module name) in parentheses after the type.

### Examples

```
feat: add health check endpoint to crewai_agent
fix: correct env var name in langgraph/react_agent
docs: update README with agentctl usage
test: add tests for tool registration
chore: bump python-dotenv in pyproject.toml
```

This is optional but appreciated; maintainers may ask you to reword commits when preparing a release.

## Questions?

See the main [README](README.md) or open an issue. You can also contact [wrebisz@redhat.com](mailto:wrebisz@redhat.com) or [tguzik@redhat.com](mailto:tguzik@redhat.com).
