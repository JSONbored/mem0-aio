#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def _add_local_aio_fleet() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    for candidate in (
        repo_root / ".aio-fleet" / "src",
        repo_root.parent / "aio-fleet" / "src",
    ):
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            return


def main() -> int:
    _add_local_aio_fleet()
    try:
        from aio_fleet.release import main as release_main
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "aio_fleet.release is required. Run from the standard workspace with "
            "../aio-fleet present, or let the reusable aio-fleet workflows check "
            "out .aio-fleet before invoking this shim."
        ) from exc

    return int(
        release_main(
            ["--repo-path", str(Path(__file__).resolve().parents[1]), *sys.argv[1:]]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
