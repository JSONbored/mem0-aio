#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class CiFlags:
    run_tests_requested: bool
    publish_requested: bool


def resolve_flags(
    event_name: str,
    ref: str,
) -> CiFlags:
    if event_name == "push" and ref == "refs/heads/main":
        return CiFlags(run_tests_requested=True, publish_requested=True)

    if event_name == "pull_request":
        return CiFlags(run_tests_requested=True, publish_requested=False)

    if event_name == "workflow_dispatch":
        return CiFlags(run_tests_requested=True, publish_requested=False)

    return CiFlags(run_tests_requested=False, publish_requested=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve CI gate flags for build workflow."
    )
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--ref", required=True)
    args = parser.parse_args()

    flags = resolve_flags(
        event_name=args.event_name,
        ref=args.ref,
    )
    print(f"run_tests_requested={'true' if flags.run_tests_requested else 'false'}")
    print(f"publish_requested={'true' if flags.publish_requested else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
