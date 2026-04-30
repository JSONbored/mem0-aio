from __future__ import annotations

from pathlib import Path

PUBLISH_WORKFLOW = Path(".github/workflows/publish-release.yml")


def test_release_target_lookup_lives_in_pinned_fleet_workflow() -> None:
    workflow = PUBLISH_WORKFLOW.read_text()

    assert (  # nosec B101
        "uses: JSONbored/aio-fleet/.github/workflows/aio-publish-release.yml@"
        in workflow
    )
    assert "@main" not in workflow  # nosec B101
    assert "scripts/release.py find-release-target-commit" not in workflow  # nosec B101
    assert "fetch-depth: 0" not in workflow  # nosec B101

    optional_agent_publish = Path(".github/workflows/publish-release-agent.yml")
    if optional_agent_publish.exists():
        agent_workflow = optional_agent_publish.read_text()
        assert (  # nosec B101
            "uses: JSONbored/aio-fleet/.github/workflows/aio-publish-release.yml@"
            in agent_workflow
        )
        assert "@main" not in agent_workflow  # nosec B101
        assert (
            "scripts/release.py find-release-target-commit" not in agent_workflow
        )  # nosec B101
        assert "fetch-depth: 0" not in agent_workflow  # nosec B101
