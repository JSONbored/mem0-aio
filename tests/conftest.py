from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.helpers import build_test_image, docker_available

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_TAG = os.environ.get("AIO_TEST_IMAGE", "mem0-aio:pytest")
API_SOURCE = REPO_ROOT / "openmemory/openmemory/api"


@pytest.fixture(scope="session")
def built_image() -> str:
    if not docker_available():
        pytest.skip("Docker is unavailable; integration tests require Docker/OrbStack.")
    if not API_SOURCE.exists():
        pytest.fail(
            "Mem0 source submodule is missing. Run 'git submodule update --init --recursive'."
        )
    build_test_image(IMAGE_TAG)
    return IMAGE_TAG
