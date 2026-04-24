from __future__ import annotations

from pathlib import Path


def test_publish_checkout_fetches_full_history_before_release_target_lookup() -> None:
    workflow = Path(".github/workflows/build.yml").read_text()
    release_lookup = (
        'release_target="$(python3 scripts/release.py find-release-target-commit'
    )
    release_lookup_index = workflow.index(release_lookup)
    checkout_index = workflow.rfind("uses: actions/checkout@", 0, release_lookup_index)

    assert checkout_index != -1  # nosec B101

    checkout_block = workflow[checkout_index:release_lookup_index]

    assert "fetch-depth: 0" in checkout_block  # nosec B101
