#!/bin/bash
# =============================================================================
# Claude Code Container Entrypoint
# =============================================================================
#
# This script handles environment setup before running Claude Code.
# It configures authentication, MCP servers, and other runtime settings
# based on environment variables passed to the container.
#
# Supported Environment Variables:
#
#   Authentication:
#     ANTHROPIC_API_KEY        - API key for Anthropic (or compatible endpoint)
#     ANTHROPIC_BASE_URL       - Custom API endpoint (vLLM, OGX, etc.)
#
#   Vertex AI Authentication (alternative to ANTHROPIC_API_KEY):
#     CLAUDE_CODE_USE_VERTEX       - Set to "1" to enable Vertex AI mode
#     ANTHROPIC_VERTEX_PROJECT_ID  - GCP project ID with Vertex AI access
#     CLOUD_ML_REGION              - Vertex AI region (e.g., us-east5, global)
#     GOOGLE_APPLICATION_CREDENTIALS - Path to GCP service account key JSON
#
#   Model Configuration:
#     CLAUDE_MODEL             - Model to use (e.g., sonnet, opus, claude-sonnet-4-5-20250929)
#
#   MCP Configuration:
#     MCP_CONFIG_FILE          - Path to MCP configuration JSON file
#     MCP_CONFIG_JSON          - MCP configuration as inline JSON string
#
#   Skills Configuration:
#     SKILLS_DIR               - Path to skills directory (default: /opt/skills)
#
#   Permissions:
#     SKIP_PERMISSIONS         - Set to "true" to bypass permission checks (sandboxed environments only)
#
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

log_info() {
    echo "[entrypoint] INFO: $*" >&2
}

log_warn() {
    echo "[entrypoint] WARN: $*" >&2
}

log_error() {
    echo "[entrypoint] ERROR: $*" >&2
}

# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

validate_environment() {
    # Check for API key (required unless using alternative auth)
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        log_warn "ANTHROPIC_API_KEY not set. Claude Code may not be able to authenticate."
        log_warn "Set ANTHROPIC_API_KEY or ensure alternative authentication is configured."
    fi

    # Log API endpoint if custom
    if [[ -n "${ANTHROPIC_BASE_URL:-}" ]]; then
        log_info "Using custom API endpoint: ${ANTHROPIC_BASE_URL}"
    fi

    # Log model if specified
    if [[ -n "${CLAUDE_MODEL:-}" ]]; then
        log_info "Using model: ${CLAUDE_MODEL}"
    fi
}

# -----------------------------------------------------------------------------
# MCP Configuration
# -----------------------------------------------------------------------------

setup_mcp() {
    local mcp_args=()

    # MCP config from file
    if [[ -n "${MCP_CONFIG_FILE:-}" ]]; then
        if [[ -f "${MCP_CONFIG_FILE}" ]]; then
            log_info "Loading MCP config from file: ${MCP_CONFIG_FILE}"
            mcp_args+=("--mcp-config" "${MCP_CONFIG_FILE}")
        else
            log_error "MCP_CONFIG_FILE specified but not found: ${MCP_CONFIG_FILE}"
            exit 1
        fi
    fi

    # MCP config from inline JSON
    if [[ -n "${MCP_CONFIG_JSON:-}" ]]; then
        log_info "Loading MCP config from environment variable"
        mcp_args+=("--mcp-config" "${MCP_CONFIG_JSON}")
    fi

    # Export for use in command building
    export MCP_ARGS="${mcp_args[*]:-}"
}

# -----------------------------------------------------------------------------
# Skills Configuration
# -----------------------------------------------------------------------------

setup_skills() {
    local skills_dir="${SKILLS_DIR:-/opt/skills}"

    # Check if skills directory exists and has SKILL.md files
    # Claude Code expects skills as directories containing SKILL.md files
    # Structure: /opt/skills/<skill-name>/SKILL.md
    if [[ -d "${skills_dir}" ]]; then
        local skill_count
        skill_count=$(find "${skills_dir}" -name "SKILL.md" -type f 2>/dev/null | wc -l)
        if [[ ${skill_count} -gt 0 ]]; then
            log_info "Found ${skill_count} skill(s) in ${skills_dir}"
            export SKILLS_DIR_FOUND="${skills_dir}"
        else
            log_info "Skills directory is empty (no SKILL.md files found): ${skills_dir}"
        fi
    else
        log_info "Skills directory not found: ${skills_dir}"
    fi
}

# -----------------------------------------------------------------------------
# Build Command Arguments
# -----------------------------------------------------------------------------

build_claude_args() {
    local args=()

    # Model selection
    if [[ -n "${CLAUDE_MODEL:-}" ]]; then
        args+=("--model" "${CLAUDE_MODEL}")
    fi

    # MCP configuration
    if [[ -n "${MCP_ARGS:-}" ]]; then
        # shellcheck disable=SC2206
        args+=(${MCP_ARGS})
    fi

    # Skills directory - use --add-dir to make skills discoverable
    # Claude Code looks for SKILL.md files in added directories
    if [[ -n "${SKILLS_DIR_FOUND:-}" ]]; then
        args+=("--add-dir" "${SKILLS_DIR_FOUND}")
    fi

    # Permission bypass for sandboxed environments
    if [[ "${SKIP_PERMISSIONS:-false}" == "true" ]]; then
        log_warn "Permission checks disabled (SKIP_PERMISSIONS=true)"
        args+=("--dangerously-skip-permissions")
    fi

    # Add workspace directory access
    args+=("--add-dir" "/workspace")

    # Export for use in exec
    export CLAUDE_EXTRA_ARGS="${args[*]:-}"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    log_info "Starting Claude Code container"
    log_info "Claude Code version: $(claude --version 2>/dev/null || echo 'unknown')"

    # Run setup functions
    validate_environment
    setup_mcp
    setup_skills
    build_claude_args

    # If no arguments provided, show help
    if [[ $# -eq 0 ]]; then
        log_info "No command provided. Running: claude --help"
        exec claude --help
    fi

    # If first argument is "claude", run it with our extra args
    if [[ "$1" == "claude" ]]; then
        shift
        log_info "Running: claude ${CLAUDE_EXTRA_ARGS} $*"
        # shellcheck disable=SC2086
        exec claude ${CLAUDE_EXTRA_ARGS} "$@"
    fi

    # Otherwise, run the command as-is (allows running bash, sh, etc.)
    log_info "Running: $*"
    exec "$@"
}

main "$@"
