from __future__ import annotations

import logging

import pytest

from integration.utils import (
    MakeTargetError,
    get_route,
    health_check,
    run_make,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "langgraph-react-agent"
INTERNAL_REGISTRY = "image-registry.openshift-image-registry.svc:5000"


@pytest.fixture(scope="module")
def agent_dir(repo_root):
    return repo_root / "agents" / "langgraph" / "react_agent"


@pytest.fixture(scope="module")
def deployed_agent(cluster_auth, agent_dir):
    namespace = cluster_auth["namespace"]
    container_image = f"{INTERNAL_REGISTRY}/{namespace}/{AGENT_NAME}:latest"
    deploy_env = {"CONTAINER_IMAGE": container_image}

    deployed = False
    try:
        logger.info("Building image on cluster via build-openshift...")
        run_make("build-openshift", cwd=agent_dir, timeout=600)

        logger.info("Deploying to cluster...")
        run_make("deploy", cwd=agent_dir, timeout=300, env=deploy_env)
        deployed = True

        route_url = get_route(AGENT_NAME)
        logger.info("Agent deployed at %s", route_url)

        yield route_url

    except MakeTargetError as exc:
        pytest.fail(f"Deployment failed at make {exc.target}: {exc}")

    finally:
        if deployed:
            logger.info("Tearing down deployment...")
            try:
                run_make("undeploy", cwd=agent_dir, timeout=120)
            except MakeTargetError:
                logger.warning("Cleanup failed — manual undeploy may be needed", exc_info=True)


@pytest.mark.integration
def test_health_endpoint(deployed_agent):
    route_url = deployed_agent
    result = health_check(f"{route_url}/health", retries=12, backoff=5.0)

    assert result["status"] == "healthy"
    assert result["agent_initialized"] is True
