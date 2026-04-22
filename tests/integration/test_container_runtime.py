from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.conftest import IMAGE_TAG
from tests.helpers import reserve_host_port, run_command

pytestmark = pytest.mark.integration


def logs(name: str) -> str:
    result = run_command(["docker", "logs", name], check=False)
    return result.stdout + result.stderr


def wait_for_ready(name: str, ui_port: int, api_port: int, qdrant_port: int) -> None:
    deadline = time.time() + 240
    while time.time() < deadline:
        status = run_command(
            ["docker", "inspect", "-f", "{{.State.Status}}", name],
            check=False,
        ).stdout.strip()
        if status != "running":
            raise AssertionError(f"{name} stopped before becoming ready.\n{logs(name)}")

        if (
            run_command(
                ["curl", "-fsS", f"http://127.0.0.1:{ui_port}/"], check=False
            ).returncode
            == 0
            and run_command(
                ["curl", "-fsS", f"http://127.0.0.1:{api_port}/api/v1/config/"],
                check=False,
            ).returncode
            == 0
            and run_command(
                ["curl", "-fsS", f"http://127.0.0.1:{qdrant_port}/readyz"],
                check=False,
            ).returncode
            == 0
        ):
            return
        time.sleep(2)

    raise AssertionError(f"{name} did not become ready.\n{logs(name)}")


@contextmanager
def container(storage_dir: Path):
    name = f"mem0-aio-pytest-{uuid.uuid4().hex[:10]}"
    ui_port = reserve_host_port()
    api_port = reserve_host_port()
    qdrant_port = reserve_host_port()
    command = [
        "docker",
        "run",
        "-d",
        "--platform",
        "linux/amd64",
        "--name",
        name,
        "-p",
        f"{ui_port}:3000",
        "-p",
        f"{api_port}:8765",
        "-p",
        f"{qdrant_port}:6333",
        "-v",
        f"{storage_dir}:/mem0/storage",
        IMAGE_TAG,
    ]
    run_command(command)
    try:
        yield name, ui_port, api_port, qdrant_port
    finally:
        run_command(["docker", "rm", "-f", name], check=False)


def test_happy_path_boot_and_restart(built_image: str) -> None:
    with TemporaryDirectory(prefix="mem0-aio-storage-") as storage_dir:
        with container(Path(storage_dir)) as (name, ui_port, api_port, qdrant_port):
            wait_for_ready(name, ui_port, api_port, qdrant_port)
            run_command(
                [
                    "curl",
                    "-fsS",
                    f"http://127.0.0.1:{ui_port}/openmemory-api/api/v1/config",
                ]
            )
            assert Path(storage_dir, "openmemory.db").is_file()  # nosec B101

            run_command(["docker", "restart", name])
            wait_for_ready(name, ui_port, api_port, qdrant_port)
            assert Path(storage_dir, "openmemory.db").is_file()  # nosec B101
