from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import docker_available, ensure_pytest_image

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_TAG = "mem0-aio:pytest"
API_SOURCE = REPO_ROOT / "openmemory/openmemory/api"


@pytest.fixture(scope="session")
def built_image() -> str:
    if not docker_available():
        pytest.skip("Docker is unavailable; integration tests require Docker/OrbStack.")
    if not API_SOURCE.exists():
        pytest.fail(
            "Mem0 source submodule is missing. Run 'git submodule update --init --recursive'."
        )
    ensure_pytest_image(IMAGE_TAG)
    return IMAGE_TAG
