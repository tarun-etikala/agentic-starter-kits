# Verify Traces After Tracing Integration

> **Usage:** `/project:verify-traces <agent_path>`
> **Example:** `/project:verify-traces agents/autogen/chat_agent`

You are verifying that MLflow tracing works correctly after integrating it into a new agent template. This is the final validation step in the tracing integration workflow.

## Input

You need:
1. **Agent path**: The agent directory (e.g., `agents/autogen/chat_agent/`)
2. **Coverage level**: A, B, or C (from the autolog support report)

## Important

You must execute every step yourself — do NOT tell the user to do it manually or suggest they run commands. You are responsible for running all commands, starting servers, sending requests, and inspecting traces. Do not stop partway through and summarize what the user should do next.

## Steps

### 1. Code review

Read and execute every step in the `review-tracing-code` skill yourself. Read the agent's `tracing.py`, `main.py`, and any manual wrapping files. Check each item in the review checklist and produce the code review report.

### 2. Live trace testing

Read and execute every step in the `test-tracing` skill yourself. This means YOU must:
- Check if MLflow is installed and install it if not
- Set up the agent's `.env` from `.env.example`
- Start the MLflow server (finding an open port)
- Start the agent
- Send test requests (both streaming and non-streaming)
- Query the MLflow API to verify traces appeared
- Inspect spans and validate them

Do not skip any of these steps or ask the user to do them.

### 3. Combined report

Combine the outputs from both steps into a single verification report:

```
## Tracing Verification Report: <agent_name>

### Code Review
<output from review-tracing-code>

### Live Test Results
<output from test-tracing>

### Overall Status: PASS / FAIL
```

If FAIL, list specific issues and which skill to re-run to fix them (e.g., "Missing tool wrapping in streaming path — re-run `add-manual-tracing`").

## Self-Update (mandatory)

**Before finishing, you MUST check whether this skill file needs updating.** This is not optional. If any of the following are true, update this file immediately:

- You deviated from these instructions because they were inaccurate, outdated, or insufficient — and your deviation worked.
- You encountered a new pattern not covered here (e.g., a framework that uses OpenTelemetry instead of autolog, or a new provider path). Add it as a variant under the existing levels (A, B, or C) rather than introducing new levels.
- File paths, function names, or API patterns referenced here have changed.
- A step didn't work as described and needed a different approach.

If nothing needed changing, move on. But do not skip this check.
