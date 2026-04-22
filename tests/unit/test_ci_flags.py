from __future__ import annotations

from scripts.ci_flags import resolve_flags


def test_ci_flag_resolution_matrix() -> None:
    cases = [
        ("push", "refs/heads/main", True, True),
        ("push", "refs/heads/feature", False, False),
        ("pull_request", "refs/pull/1/merge", True, False),
        ("workflow_dispatch", "refs/heads/main", True, False),
        ("workflow_dispatch", "refs/heads/feature", True, False),
    ]

    for event_name, ref, expected_test, expected_publish in cases:
        result = resolve_flags(event_name=event_name, ref=ref)
        assert result.run_tests_requested is expected_test  # nosec B101
        assert result.publish_requested is expected_publish  # nosec B101
