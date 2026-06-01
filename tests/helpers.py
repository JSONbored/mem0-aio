from __future__ import annotations

from pathlib import Path

from aio_fleet.app_testing import *  # noqa: F403
from aio_fleet.app_testing import configure_repo_root, run_command

REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_OLLAMA_PATH = REPO_ROOT / "tests" / "fixtures" / "mock_ollama.py"

configure_repo_root(REPO_ROOT)


def relax_container_written_path(path: Path) -> None:
    run_command(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{path}:/target",
            "python:3.13-alpine",
            "sh",
            "-lc",
            "chmod -R a+rwX /target || true",
        ],
        check=False,
    )


def start_mock_ollama_container(
    container_name: str, *, network_name: str | None = None
) -> None:
    command = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
    ]
    if network_name is not None:
        command.extend(["--network", network_name])
    command.extend(
        [
            "-v",
            f"{MOCK_OLLAMA_PATH}:/mock_ollama.py:ro",
            "python:3.13-alpine",
            "python",
            "-u",
            "/mock_ollama.py",
        ]
    )
    run_command(command)
