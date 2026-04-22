from __future__ import annotations

from tests.conftest import REPO_ROOT
from tests.helpers import pytest_env, run_command


def test_validate_derived_repo_script_passes_with_strict_placeholders() -> None:
    env = pytest_env()
    env["STRICT_PLACEHOLDERS"] = "true"
    result = run_command(
        ["bash", "scripts/validate-derived-repo.sh", "."],
        cwd=REPO_ROOT,
        env=env,
    )
    assert "Derived repo validation passed." in result.stdout  # nosec B101
