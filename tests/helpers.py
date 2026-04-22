from __future__ import annotations

import os
import shutil
import socket
import subprocess  # nosec B404 - test helpers shell out only to local tooling
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603 - tests execute trusted local commands only
        command,
        cwd=cwd or REPO_ROOT,
        env=env,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False

    result = run_command(["docker", "info"], check=False)
    return result.returncode == 0


def docker_image_exists(image_tag: str) -> bool:
    result = run_command(["docker", "image", "inspect", image_tag], check=False)
    return result.returncode == 0


def ensure_pytest_image(image_tag: str) -> None:
    if os.environ.get("AIO_PYTEST_USE_PREBUILT_IMAGE") == "true":
        if not docker_image_exists(image_tag):
            raise AssertionError(
                f"Expected prebuilt pytest image {image_tag} to be loaded before the test run."
            )
        return

    run_command(["docker", "build", "--platform", "linux/amd64", "-t", image_tag, "."])


def reserve_host_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock.getsockname()[1]


class DockerRuntime:
    def __init__(self, image_tag: str) -> None:
        self.image_tag = image_tag

    def build(self) -> None:
        ensure_pytest_image(self.image_tag)

    def inspect_state(self, name: str, field: str) -> str:
        result = run_command(
            ["docker", "inspect", "-f", f"{{{{.{field}}}}}", name],
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    def logs(self, name: str) -> str:
        result = run_command(["docker", "logs", name], check=False)
        return result.stdout + result.stderr

    def remove(self, name: str) -> None:
        run_command(["docker", "rm", "-f", name], check=False)

    @contextmanager
    def container(
        self,
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> Iterator["ContainerHandle"]:
        suffix = uuid.uuid4().hex[:10]
        name = f"aio-template-pytest-{suffix}"
        http_port = reserve_host_port()

        with TemporaryDirectory(
            prefix=f"{name}-config-"
        ) as config_dir, TemporaryDirectory(prefix=f"{name}-data-") as data_dir:
            command = [
                "docker",
                "run",
                "-d",
                "--platform",
                "linux/amd64",
                "--name",
                name,
                "-p",
                f"{http_port}:8080",
                "-v",
                f"{config_dir}:/config",
                "-v",
                f"{data_dir}:/data",
            ]

            if env_overrides:
                for key, value in env_overrides.items():
                    command.extend(["-e", f"{key}={value}"])

            command.append(self.image_tag)
            run_command(command)
            handle = ContainerHandle(
                runtime=self,
                name=name,
                http_port=http_port,
                config_dir=Path(config_dir),
                data_dir=Path(data_dir),
            )
            try:
                yield handle
            finally:
                self.remove(name)


class ContainerHandle:
    def __init__(
        self,
        *,
        runtime: DockerRuntime,
        name: str,
        http_port: int,
        config_dir: Path,
        data_dir: Path,
    ) -> None:
        self.runtime = runtime
        self.name = name
        self.http_port = http_port
        self.config_dir = config_dir
        self.data_dir = data_dir

    def logs(self) -> str:
        return self.runtime.logs(self.name)

    def exec(self, command: str) -> subprocess.CompletedProcess[str]:
        return run_command(["docker", "exec", self.name, "sh", "-lc", command])

    def restart(self) -> None:
        run_command(["docker", "restart", self.name])

    def is_running(self) -> bool:
        return self.runtime.inspect_state(self.name, "State.Status") == "running"

    def wait_for_http(self, *, path: str = "/health", timeout: int = 180) -> None:
        deadline = time.time() + timeout
        url = f"http://127.0.0.1:{self.http_port}{path}"

        while time.time() < deadline:
            if not self.is_running():
                raise AssertionError(
                    f"{self.name} stopped before HTTP became healthy.\nLogs:\n{self.logs()}"
                )

            result = run_command(["curl", "-fsS", url], check=False)
            if result.returncode == 0:
                return
            time.sleep(2)

        raise AssertionError(
            f"{self.name} did not become healthy.\nLogs:\n{self.logs()}"
        )


def pytest_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env
