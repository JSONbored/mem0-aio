from __future__ import annotations

import subprocess  # nosec B404
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_shared_release_shim_loads() -> None:
    result = subprocess.run(  # nosec B603
        [sys.executable, "scripts/release.py", "has-unreleased-changes"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr  # nosec B101
    assert result.stdout.strip() in {"true", "false"}  # nosec B101
