from __future__ import annotations

import time
import uuid
from contextlib import contextmanager

import pytest

from tests.conftest import IMAGE_TAG
from tests.helpers import (
    container_path_exists,
    docker_volume,
    reserve_host_port,
    run_command,
)

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
def container(storage_volume: str):
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
        f"{storage_volume}:/mem0/storage",
        IMAGE_TAG,
    ]
    run_command(command)
    try:
        yield name, ui_port, api_port, qdrant_port
    finally:
        run_command(["docker", "rm", "-f", name], check=False)


def test_happy_path_boot_and_restart(built_image: str) -> None:
    with docker_volume("mem0-aio-storage") as storage_volume:
        with container(storage_volume) as (name, ui_port, api_port, qdrant_port):
            wait_for_ready(name, ui_port, api_port, qdrant_port)
            run_command(
                [
                    "curl",
                    "-fsS",
                    f"http://127.0.0.1:{ui_port}/openmemory-api/api/v1/config",
                ]
            )
            memory_proxy_status = run_command(
                [
                    "curl",
                    "-sS",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    "-X",
                    "POST",
                    "-H",
                    "Content-Type: application/json",
                    "-d",
                    "{}",
                    f"http://127.0.0.1:{ui_port}/openmemory-api/api/v1/memories",
                ]
            ).stdout
            assert memory_proxy_status == "422"  # nosec B101
            assert container_path_exists(
                name, "/mem0/storage/openmemory.db"
            )  # nosec B101

            run_command(["docker", "restart", name])
            wait_for_ready(name, ui_port, api_port, qdrant_port)
            assert container_path_exists(
                name, "/mem0/storage/openmemory.db"
            )  # nosec B101


def test_competing_vector_store_config_exits(built_image: str) -> None:
    name = f"mem0-aio-invalid-vector-{uuid.uuid4().hex[:10]}"
    result = run_command(
        [
            "docker",
            "run",
            "--name",
            name,
            "--platform",
            "linux/amd64",
            "-e",
            "REDIS_URL=redis://redis:6379/0",
            "-e",
            "PG_HOST=postgres",
            "-e",
            "PG_PORT=5432",
            "-e",
            "QDRANT_URL=http://qdrant:6333",
            built_image,
        ],
        check=False,
    )
    try:
        output = result.stdout + result.stderr
        assert result.returncode == 1  # nosec B101
        assert "choose exactly one vector store backend" in output  # nosec B101
        assert "redis pgvector qdrant" in output  # nosec B101
    finally:
        run_command(["docker", "rm", "-f", name], check=False)
