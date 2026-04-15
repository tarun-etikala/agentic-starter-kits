# Error Diagnosis Reference

Read this file when a phase encounters an error. Find the relevant phase and error pattern below.

## Table of Contents

1. [Phase 3: Login Errors](#phase-3-login-errors)
2. [Phase 5: Build Errors](#phase-5-build-errors)
3. [Phase 6: Deploy Errors](#phase-6-deploy-errors)
4. [Phase 7: Verification Errors](#phase-7-verification-errors)

---

## Phase 3: Login Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `error: You must be logged in` | oc session expired | Re-run `oc login --token=<token> --server=<url>` |
| `error: x509: certificate signed by unknown authority` | Self-signed cluster cert | Add `--insecure-skip-tls-verify` to oc login (not recommended for production) |
| `Forbidden` on `oc projects` | User lacks project list permissions | User can still deploy to known projects — ask for project name directly |

## Phase 5: Build Errors

### Local build (`make build`)

| Error pattern | Cause | Fix |
|---------------|-------|-----|
| `neither podman nor docker found` | No container CLI in PATH | Install podman or docker, or use `make build-openshift` |
| `CONTAINER_IMAGE is not set` | Missing from .env | Set CONTAINER_IMAGE in .env |
| `Error: Dockerfile not found` | Wrong working directory | Verify cwd is the agent directory |
| `no space left on device` | Disk full | Run `podman system prune` or `docker system prune` |
| `platform linux/amd64` errors on Apple Silicon | Cross-platform build issue | Makefile already sets `--platform linux/amd64` — if still failing, check podman/docker version |

### Push (`make push`)

| Error pattern | Cause | Fix |
|---------------|-------|-----|
| `unauthorized` / `access denied` | Not logged into registry | Run `podman login <registry>` |
| `repository does not exist` | Registry namespace doesn't exist | Create the repository on the registry first |
| `denied: requested access` | Wrong credentials or no push permission | Verify registry credentials and permissions |

### In-cluster build (`make build-openshift`)

| Error pattern | Cause | Fix |
|---------------|-------|-----|
| `forbidden` | Insufficient namespace permissions | Need `edit` or `admin` role on the project |
| Build timeout | Large image or slow cluster | Check `oc logs bc/<agent-name>` for progress |
| `push to image stream failed` | Internal registry issue | Check `oc get is` and registry status |

## Phase 6: Deploy Errors

### Helm errors

| Error pattern | Cause | Fix |
|---------------|-------|-----|
| `Error: INSTALLATION FAILED` | Usually missing values | Check all required env vars are set in .env |
| `rendered manifests contain a resource that already exists` | Stale resources | Run `make undeploy`, then retry `make deploy` |
| `chart not found` | Wrong CHART_DIR path | Verify running from agent directory (Makefile uses relative path `../../../charts/agent`) |

### Pod failures

| Pod status | Cause | Diagnostic command | Fix |
|------------|-------|-------------------|-----|
| `ImagePullBackOff` | Can't pull image | `oc describe pod -l app.kubernetes.io/name=<agent>` | Make image public or add pull secret |
| `CrashLoopBackOff` | App crashes on start | `oc logs deployment/<agent> --tail=50` | Usually bad env vars — check API_KEY, BASE_URL, MODEL_ID |
| `Pending` | No resources | `oc describe pod -l app.kubernetes.io/name=<agent>` | Reduce resource requests in values.yaml or free cluster resources |
| `ErrImagePull` | Image/tag not found | `oc describe pod -l app.kubernetes.io/name=<agent>` | Verify CONTAINER_IMAGE matches pushed image exactly |
| `CreateContainerConfigError` | Secret or configmap missing | `oc describe pod -l app.kubernetes.io/name=<agent>` | Re-run `make deploy` — Helm may not have created secrets |

## Phase 7: Verification Errors

### Health check failures

| Scenario | Diagnosis | Fix |
|----------|-----------|-----|
| Timeout / connection refused | Pod not ready yet | Wait longer — pods can take 60-90s. Check: `oc get pods -l app.kubernetes.io/name=<agent>` |
| HTTP 503 | Route exists but no backend | Pod may be starting or crashed. Check pod status and logs |
| HTTP 502 | Router can't reach pod | Check service: `oc get svc <agent>` — port should be 8080 |
| SSL error | TLS termination issue | Route uses edge TLS by default. Ensure using `https://` |

### /chat/completions failures

| Scenario | Likely cause | Diagnosis | Fix |
|----------|-------------|-----------|-----|
| HTTP 401/403 | Bad API_KEY | Pod logs will show auth error | Update API_KEY in .env and redeploy |
| HTTP 500 | Agent code error or model timeout | `oc logs deployment/<agent> --tail=50` | Check if MODEL_ID is valid for the endpoint |
| Timeout (>30s) | Model endpoint slow | Check if model service is healthy | Try a smaller/faster model, or increase timeout |
| Connection error from pod | BASE_URL unreachable from cluster | Pod logs: "connection refused" to BASE_URL | BASE_URL must be accessible from inside the cluster. For local URLs, use cluster-internal service URLs |
| Empty `content` in response | Model returned empty response | Try a different prompt or model | Verify MODEL_ID is correct |
| JSON parse error | Non-OpenAI-compatible endpoint | Check response format | Ensure endpoint is OpenAI-compatible (returns `choices[0].message.content`) |

### General debugging commands

```bash
# Full pod details
oc describe pod -l app.kubernetes.io/name=<agent-name>

# Stream live logs
oc logs -f deployment/<agent-name>

# Check events in namespace
oc get events --sort-by='.lastTimestamp' | tail -20

# Exec into pod for debugging
oc exec deployment/<agent-name> -- env | grep -E 'API_KEY|BASE_URL|MODEL_ID'

# Check if model endpoint is reachable from inside the pod
oc exec deployment/<agent-name> -- curl -s --max-time 5 "${BASE_URL}/models"
```
