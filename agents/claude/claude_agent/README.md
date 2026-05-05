# How to Deploy Claude Code on OpenShift

A step-by-step guide to build, test, and deploy the Claude Code container image.

## Prerequisites

- `podman` installed locally
- `oc` CLI installed and logged into your OpenShift cluster
- An Anthropic API key OR a GCP service account key for Vertex AI
- The Containerfile and entrypoint.sh files

---

## Option A: Deploy with Anthropic API Key

### 0. Get your Anthropic API key

1. Go to [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to **API Keys** in the left sidebar
4. Click **Create Key** and give it a name
5. Copy the key (it starts with `sk-ant-api03-...`)

**Note**: You need a paid account with credits to use the API.

### 1. Build and test locally

```bash
# Build
podman build -t claude-code:latest -f Containerfile .

# Test (non-interactive)
podman run --rm \
  -e ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY_HERE" \
  claude-code:latest \
  claude -p "What is 2+2?"
```

### 2. Create OpenShift namespace

```bash
oc new-project my-claude-project
```

### 3. Create the API key secret

```bash
oc create secret generic claude-credentials \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY_HERE"
```

### 4. Apply the deployment manifest

```bash
oc apply -f deployment.yaml
```

### 5. Build the image on OpenShift

```bash
oc start-build claude-code --from-dir=. --follow
```

### 6. Wait for deployment and test

```bash
# Wait for rollout
oc rollout status deployment/claude-code

# Test (non-interactive)
oc exec deployment/claude-code -- bash -c '
  export HOME=/home/claude-agent
  claude -p "What is 2+2?"
'
```

### 7. Interactive mode (optional)

For a full interactive Claude Code experience with multi-turn conversations:

```bash
# Local interactive mode
podman run -it --rm \
  -e ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY_HERE" \
  -v $(pwd):/workspace:z \
  claude-code:latest \
  claude

# OpenShift interactive mode
oc exec -it deployment/claude-code -- bash -c '
  export HOME=/home/claude-agent
  cd /workspace
  claude
'
```

**Note**: Interactive mode requires a TTY, so use `-it` flags with podman and `oc exec`.

### 8. Debug mode (optional)

To see detailed logging of Claude Code activity, use the `--debug` flag:

```bash
# Enable full debug logging
oc exec -it deployment/claude-code -- bash -c '
  export HOME=/home/claude-agent
  cd /workspace
  claude --debug
'

# Enable debug logging for API calls only
oc exec -it deployment/claude-code -- bash -c '
  export HOME=/home/claude-agent
  cd /workspace
  claude --debug api
'
```

Debug logs are written to a file. To monitor the logs in real-time, open a second terminal and run:

```bash
oc exec deployment/claude-code -- bash -c 'tail -f /home/claude-agent/.claude/debug/*.txt'
```

---

## Option B: Deploy with Vertex AI

### 0. Get your GCP service account key

You need a GCP service account with Vertex AI access. Choose one of these methods:

**Option 1: Create a new service account in GCP Console**

1. Go to [GCP Console](https://console.cloud.google.com)
2. Select your project (must have Vertex AI API enabled)
3. Navigate to **IAM & Admin → Service Accounts**
4. Click **+ CREATE SERVICE ACCOUNT**
   - Name: `claude-code-user` (or your preferred name)
   - Grant role: **Vertex AI User** (`roles/aiplatform.user`)
5. Click on the service account → **Keys** tab
6. Click **Add Key → Create new key → JSON**
7. The key file downloads automatically - save it securely

**Option 2: Use gcloud CLI**

```bash
# Create service account
gcloud iam service-accounts create claude-code-user \
  --display-name="Claude Code User"

# Grant Vertex AI access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:claude-code-user@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create ~/claude-vertex-key.json \
  --iam-account=claude-code-user@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Note**: Creating service accounts requires **IAM Admin** or **Service Account Admin** permissions in the GCP project.

### 1. Build and test locally

```bash
# Build
podman build -t claude-code:latest -f Containerfile .

# Test (non-interactive)
podman run --rm \
  -e CLAUDE_CODE_USE_VERTEX=1 \
  -e ANTHROPIC_VERTEX_PROJECT_ID="your-gcp-project-id" \
  -e CLOUD_ML_REGION="global" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/var/secrets/google/key.json" \
  -v /path/to/your-service-account-key.json:/var/secrets/google/key.json:ro,z \
  claude-code:latest \
  claude -p "What is 2+2?"
```

### 2. Create OpenShift namespace

```bash
oc new-project my-claude-project
```

### 3. Create the GCP credentials secret

```bash
oc create secret generic claude-vertex-credentials \
  --from-file=key.json=/path/to/your-service-account-key.json
```

### 4. Apply the Vertex AI deployment manifest

```bash
oc apply -f deployment-vertex.yaml
```

### 5. Update the ConfigMap with your project details

```bash
oc patch configmap claude-vertex-config \
  -p '{"data":{"ANTHROPIC_VERTEX_PROJECT_ID":"your-gcp-project-id","CLOUD_ML_REGION":"global"}}'
```

### 6. Build the image on OpenShift

```bash
oc start-build claude-code --from-dir=. --follow
```

### 7. Wait for deployment and test

```bash
oc rollout status deployment/claude-code-vertex

# Test (non-interactive)
oc exec deployment/claude-code-vertex -- bash -c '
  export HOME=/home/claude-agent
  claude -p "What is 2+2?"
'
```

### 8. Interactive mode (optional)

For a full interactive Claude Code experience with multi-turn conversations:

```bash
# Local interactive mode
podman run -it --rm \
  -e CLAUDE_CODE_USE_VERTEX=1 \
  -e ANTHROPIC_VERTEX_PROJECT_ID="your-gcp-project-id" \
  -e CLOUD_ML_REGION="global" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/var/secrets/google/key.json" \
  -v /path/to/your-service-account-key.json:/var/secrets/google/key.json:ro,z \
  -v $(pwd):/workspace:z \
  claude-code:latest \
  claude

# OpenShift interactive mode
oc exec -it deployment/claude-code-vertex -- bash -c '
  export HOME=/home/claude-agent
  cd /workspace
  claude
'
```

**Note**: Interactive mode requires a TTY, so use `-it` flags with podman and `oc exec`.

### 9. Debug mode (optional)

To see detailed logging of Claude Code activity, use the `--debug` flag:

```bash
# Enable full debug logging
oc exec -it deployment/claude-code-vertex -- bash -c '
  export HOME=/home/claude-agent
  cd /workspace
  claude --debug
'

# Enable debug logging for API calls only
oc exec -it deployment/claude-code-vertex -- bash -c '
  export HOME=/home/claude-agent
  cd /workspace
  claude --debug api
'
```

Debug logs are written to a file. To monitor the logs in real-time, open a second terminal and run:

```bash
oc exec deployment/claude-code-vertex -- bash -c 'tail -f /home/claude-agent/.claude/debug/*.txt'
```

---

## Cleanup

```bash
oc delete deployment claude-code
oc delete buildconfig claude-code
oc delete imagestream claude-code
oc delete secret claude-credentials      # if using Anthropic API
oc delete secret claude-vertex-credentials  # if using Vertex AI
oc delete configmap claude-mcp-config
oc delete configmap claude-skills
oc delete pvc claude-workspace
oc delete project my-claude-project
```
