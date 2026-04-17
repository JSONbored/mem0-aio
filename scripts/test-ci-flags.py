#!/usr/bin/env python3
from __future__ import annotations

from ci_flags import resolve_flags


def main() -> int:
    cases = [
        ("push", "refs/heads/main", "", "", True, True),
        ("push", "refs/heads/feature", "", "", False, False),
        ("workflow_dispatch", "refs/heads/main", "true", "true", True, True),
        ("workflow_dispatch", "refs/heads/main", "1", "1", True, True),
        ("workflow_dispatch", "refs/heads/main", "false", "true", False, True),
        ("workflow_dispatch", "refs/heads/main", "", "false", False, False),
        ("workflow_dispatch", "refs/heads/main", "true", "", True, False),
        ("workflow_dispatch", "refs/heads/feature", "true", "true", False, False),
        ("pull_request", "refs/pull/1/merge", "", "", False, False),
    ]

    for idx, case in enumerate(cases, start=1):
        (
            event_name,
            ref,
            smoke_input,
            publish_input,
            expected_smoke,
            expected_publish,
        ) = case
        result = resolve_flags(
            event_name=event_name,
            ref=ref,
            run_smoke_test_input=smoke_input,
            publish_images_input=publish_input,
        )
        if result.run_smoke_requested != expected_smoke:
            raise RuntimeError(
                f"case #{idx} expected run_smoke_requested={expected_smoke}, "
                f"got {result.run_smoke_requested}"
            )
        if result.publish_requested != expected_publish:
            raise RuntimeError(
                f"case #{idx} expected publish_requested={expected_publish}, "
                f"got {result.publish_requested}"
            )

    print(f"ci_flags tests passed ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
