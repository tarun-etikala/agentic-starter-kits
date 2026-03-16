AGENT_NAME  := $(shell grep 'nameOverride' values.yaml | head -1 | awk '{print $$2}' | tr -d '"')
CHART_DIR   := ../../../charts/agent
VALUES_FILE := values.yaml

.PHONY: init run build deploy undeploy test help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

init: ## Copy .env.example to .env for configuration
	@test -f .env || cp .env.example .env
	@echo "Created .env from .env.example — edit it with your configuration"

run: ## Run agent locally with hot-reload
	@set -a && source .env && set +a && \
	  uvicorn main:app --host 0.0.0.0 --port 8080 --reload

build: ## Build and push container image
	@source .env && \
	  docker buildx build --platform linux/amd64 -t "$${CONTAINER_IMAGE}" -f Dockerfile --push .

deploy: ## Deploy to OpenShift/K8s via Helm
	@source .env && \
	  IMAGE_REPO="$${CONTAINER_IMAGE%%:*}" && \
	  IMAGE_TAG="$${CONTAINER_IMAGE##*:}" && \
	  helm upgrade --install $(AGENT_NAME) $(CHART_DIR) \
	    -f $(VALUES_FILE) \
	    --set secrets.apiKey="$${API_KEY}" \
	    --set image.repository="$${IMAGE_REPO}" \
	    --set image.tag="$${IMAGE_TAG}" \
	    --set env.BASE_URL="$${BASE_URL}" \
	    --set env.MODEL_ID="$${MODEL_ID}" \
	    --set env.EMBEDDING_MODEL="$${EMBEDDING_MODEL}" \
	    --set env.VECTOR_STORE_ID="$${VECTOR_STORE_ID}"

undeploy: ## Remove deployment from cluster
	helm uninstall $(AGENT_NAME)

test: ## Run tests
	uv run --extra dev python -m pytest tests/
