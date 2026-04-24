from __future__ import annotations

from pathlib import Path

BUILD_WORKFLOW = Path(".github/workflows/build.yml")
PYTEST_ACTION = Path(".github/actions/run-pytest/action.yml")


def test_pytest_jobs_use_shared_local_action() -> None:
    workflow = BUILD_WORKFLOW.read_text()

    assert workflow.count("uses: ./.github/actions/run-pytest") == 2  # nosec B101
    assert "Upload unit test results to Trunk" not in workflow  # nosec B101
    assert "Upload integration test results to Trunk" not in workflow  # nosec B101
    assert "trunk-io/analytics-uploader@" in PYTEST_ACTION.read_text()  # nosec B101


def test_integration_and_publish_share_docker_cache_scope() -> None:
    workflow = BUILD_WORKFLOW.read_text()

    assert "DOCKER_CACHE_SCOPE: mem0-aio-image" in workflow  # nosec B101
    assert (  # nosec B101
        workflow.count("cache-from: type=gha,scope=${{ env.DOCKER_CACHE_SCOPE }}") == 2
    )
    assert (  # nosec B101
        workflow.count(
            "cache-to: type=gha,mode=max,scope=${{ env.DOCKER_CACHE_SCOPE }}"
        )
        == 2
    )


def test_local_actions_participate_in_ci_change_detection_and_pin_checks() -> None:
    workflow = BUILD_WORKFLOW.read_text()

    assert "- .github/actions/**" in workflow  # nosec B101
    assert ".github/actions/**|.github/workflows/*)" in workflow  # nosec B101
    assert (
        'pathlib.Path(".github/actions").glob("*/action.yml")' in workflow
    )  # nosec B101
