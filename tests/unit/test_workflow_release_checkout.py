from __future__ import annotations

from pathlib import Path

BUILD_WORKFLOW = Path(".github/workflows/build.yml")


def test_release_target_lookup_lives_in_pinned_fleet_workflow() -> None:
    workflow = BUILD_WORKFLOW.read_text()

    assert (  # nosec B101
        "uses: JSONbored/aio-fleet/.github/workflows/aio-build.yml@" in workflow
    )
    assert "@main" not in workflow  # nosec B101
    assert "scripts/release.py find-release-target-commit" not in workflow  # nosec B101
    assert "fetch-depth: 0" not in workflow  # nosec B101
