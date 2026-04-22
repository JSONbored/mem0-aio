from __future__ import annotations

import sys

from tests.conftest import REPO_ROOT
from tests.helpers import run_command


def test_validate_template_script_passes() -> None:
    result = run_command(
        [sys.executable, "scripts/validate-template.py"], cwd=REPO_ROOT
    )
    assert "parsed successfully" in result.stdout  # nosec B101
