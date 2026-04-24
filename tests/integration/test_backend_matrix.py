from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib import error, request

import pytest

from tests.helpers import (
    relax_container_written_path,
    reserve_host_port,
    run_command,
    start_mock_ollama_container,
)

pytestmark = [pytest.mark.integration, pytest.mark.extended_integration]

OLLAMA_CONTAINER = os.environ.get("OLLAMA_CONTAINER", "mem0-aio-ollama-mock")
MCP_PATH = "/mcp/openmemory/http/default_user"
BACKENDS = (
    "qdrant",
    "qdrant-auth",
    "faiss",
    "chroma",
    "redis",
    "pgvector",
    "weaviate",
    "elasticsearch",
    "opensearch",
)
INVALID_LOG_MARKERS = (
    "Wrong input: Vector dimension error",
    "You didn't provide an API key",
    "Error categorizing memory",
)


def http_request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> str:
    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        request_headers.setdefault("Content-Type", "application/json")
        data = json.dumps(payload).encode()

    req = request.Request(url, data=data, headers=request_headers, method=method)
    with request.urlopen(  # nosec B310 - integration tests call only local container endpoints
        req, timeout=timeout
    ) as response:
        return response.read().decode()


def wait_http(url: str, *, timeout: int = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            http_request(url, timeout=15)
            return
        except (OSError, error.URLError):
            time.sleep(2)
    raise AssertionError(f"Timed out waiting for {url}")


def ollama_container_available() -> bool:
    return (
        run_command(["docker", "inspect", OLLAMA_CONTAINER], check=False).returncode
        == 0
    )


def backend_ready(backend: str, backend_container: str, api_port: int) -> bool:
    if backend in {"qdrant", "qdrant-auth", "faiss"}:
        return True
    if backend == "chroma":
        return (
            run_command(
                ["curl", "-fsS", f"http://127.0.0.1:{api_port}/api/v1/config/"],
                check=False,
            ).returncode
            == 0
        )
    if backend == "redis":
        return (
            run_command(
                ["docker", "exec", backend_container, "redis-cli", "ping"], check=False
            ).stdout.strip()
            == "PONG"
        )
    if backend == "pgvector":
        return (
            run_command(
                [
                    "docker",
                    "exec",
                    backend_container,
                    "pg_isready",
                    "-U",
                    "mem0",
                    "-d",
                    "mem0",
                ],
                check=False,
            ).returncode
            == 0
        )
    if backend == "weaviate":
        return (
            run_command(
                [
                    "docker",
                    "exec",
                    backend_container,
                    "wget",
                    "-qO-",
                    "http://127.0.0.1:8080/v1/.well-known/ready",
                ],
                check=False,
            ).returncode
            == 0
        )
    if backend == "elasticsearch":
        return (
            run_command(
                [
                    "docker",
                    "exec",
                    backend_container,
                    "curl",
                    "-fsSk",
                    "-u",
                    "elastic:changeme",
                    "https://127.0.0.1:9200/_cluster/health",
                ],
                check=False,
            ).returncode
            == 0
        )
    if backend == "opensearch":
        return (
            run_command(
                [
                    "docker",
                    "exec",
                    backend_container,
                    "curl",
                    "-fsSk",
                    "-u",
                    "admin:Str0ngP@ssw0rd!",
                    "https://127.0.0.1:9200/_cluster/health",
                ],
                check=False,
            ).returncode
            == 0
        )
    raise AssertionError(f"Unsupported backend {backend}")


def wait_backend_ready(backend: str, backend_container: str, api_port: int) -> None:
    timeout = 240 if backend in {"elasticsearch", "opensearch"} else 120
    deadline = time.time() + timeout
    while time.time() < deadline:
        if backend_ready(backend, backend_container, api_port):
            return
        time.sleep(2)
    raise AssertionError(f"Timed out waiting for backend {backend}")


def backend_run_command(
    backend: str,
    *,
    container_name: str,
    network_name: str,
) -> list[str] | None:
    if backend in {"qdrant", "faiss"}:
        return None
    if backend == "qdrant-auth":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "-e",
            "QDRANT__SERVICE__API_KEY=pytest-qdrant-key",
            "qdrant/qdrant:v1.17.1",
        ]
    if backend == "chroma":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "chromadb/chroma:0.6.3",
        ]
    if backend == "redis":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "redis/redis-stack-server:latest",
        ]
    if backend == "pgvector":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "-e",
            "POSTGRES_DB=mem0",
            "-e",
            "POSTGRES_USER=mem0",
            "-e",
            "POSTGRES_PASSWORD=mem0",
            "pgvector/pgvector:pg17",
        ]
    if backend == "weaviate":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "-e",
            "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
            "-e",
            "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
            "-e",
            "QUERY_DEFAULTS_LIMIT=20",
            "-e",
            "DEFAULT_VECTORIZER_MODULE=none",
            "-e",
            "ENABLE_MODULES=",
            "semitechnologies/weaviate:1.27.12",
        ]
    if backend == "elasticsearch":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "-e",
            "discovery.type=single-node",
            "-e",
            "ELASTIC_PASSWORD=changeme",
            "-e",
            "ES_JAVA_OPTS=-Xms512m -Xmx512m",
            "docker.elastic.co/elasticsearch/elasticsearch:8.15.0",
        ]
    if backend == "opensearch":
        return [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
            "-e",
            "discovery.type=single-node",
            "-e",
            "OPENSEARCH_INITIAL_ADMIN_PASSWORD=Str0ngP@ssw0rd!",
            "-e",
            "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m",
            "opensearchproject/opensearch:2.18.0",
        ]
    raise AssertionError(f"Unsupported backend {backend}")


def mem0_env_args(backend: str, backend_container: str) -> list[str]:
    env_args = [
        "-e",
        f"OLLAMA_BASE_URL=http://{OLLAMA_CONTAINER}:11434",
        "-e",
        "LLM_MODEL=tinyllama:latest",
        "-e",
        "EMBEDDER_MODEL=nomic-embed-text:latest",
    ]
    if backend == "faiss":
        env_args.extend(["-e", "FAISS_PATH=/mem0/storage/faiss"])
    elif backend == "qdrant-auth":
        env_args.extend(
            [
                "-e",
                f"QDRANT_URL=http://{backend_container}:6333",
                "-e",
                "QDRANT_API_KEY=pytest-qdrant-key",
            ]
        )
    elif backend == "chroma":
        env_args.extend(
            ["-e", f"CHROMA_HOST={backend_container}", "-e", "CHROMA_PORT=8000"]
        )
    elif backend == "redis":
        env_args.extend(["-e", f"REDIS_URL=redis://{backend_container}:6379/0"])
    elif backend == "pgvector":
        env_args.extend(
            [
                "-e",
                f"PG_HOST={backend_container}",
                "-e",
                "PG_PORT=5432",
                "-e",
                "PG_DB=mem0",
                "-e",
                "PG_USER=mem0",
                "-e",
                "PG_PASSWORD=mem0",
            ]
        )
    elif backend == "weaviate":
        env_args.extend(
            ["-e", f"WEAVIATE_HOST={backend_container}", "-e", "WEAVIATE_PORT=8080"]
        )
    elif backend == "elasticsearch":
        env_args.extend(
            [
                "-e",
                f"ELASTICSEARCH_HOST={backend_container}",
                "-e",
                "ELASTICSEARCH_PORT=9200",
                "-e",
                "ELASTICSEARCH_USER=elastic",
                "-e",
                "ELASTICSEARCH_PASSWORD=changeme",
                "-e",
                "ELASTICSEARCH_USE_SSL=true",
                "-e",
                "ELASTICSEARCH_VERIFY_CERTS=false",
            ]
        )
    elif backend == "opensearch":
        env_args.extend(
            [
                "-e",
                f"OPENSEARCH_HOST={backend_container}",
                "-e",
                "OPENSEARCH_PORT=9200",
                "-e",
                "OPENSEARCH_USER=admin",
                "-e",
                "OPENSEARCH_PASSWORD=Str0ngP@ssw0rd!",
                "-e",
                "OPENSEARCH_USE_SSL=true",
                "-e",
                "OPENSEARCH_VERIFY_CERTS=false",
            ]
        )
    return env_args


@contextmanager
def backend_runtime(backend: str, image_tag: str):
    suffix = uuid.uuid4().hex[:10]
    network_name = f"mem0-pytest-{backend}-{suffix}"
    mem0_container = f"mem0-app-{backend}-{suffix}"
    backend_container = f"mem0-backend-{backend}-{suffix}"
    ui_port = reserve_host_port()
    api_port = reserve_host_port()
    storage_dir = TemporaryDirectory(prefix=f"mem0-{backend}-storage-")

    run_command(["docker", "network", "create", network_name])
    run_command(
        ["docker", "network", "connect", network_name, OLLAMA_CONTAINER], check=False
    )

    backend_command = backend_run_command(
        backend, container_name=backend_container, network_name=network_name
    )
    if backend_command is not None:
        run_command(backend_command)

    storage_path = Path(storage_dir.name)
    if backend == "faiss":
        storage_path.joinpath("faiss").mkdir(parents=True, exist_ok=True)

    run_command(
        [
            "docker",
            "run",
            "-d",
            "--name",
            mem0_container,
            "--network",
            network_name,
            "-p",
            f"{ui_port}:3000",
            "-p",
            f"{api_port}:8765",
            "-v",
            f"{storage_path}:/mem0/storage",
            *mem0_env_args(backend, backend_container),
            image_tag,
        ]
    )

    try:
        yield {
            "backend_container": backend_container,
            "mem0_container": mem0_container,
            "ui_port": ui_port,
            "api_port": api_port,
        }
    finally:
        run_command(["docker", "rm", "-f", mem0_container], check=False)
        run_command(["docker", "rm", "-f", backend_container], check=False)
        run_command(
            ["docker", "network", "disconnect", network_name, OLLAMA_CONTAINER],
            check=False,
        )
        run_command(["docker", "network", "rm", network_name], check=False)
        relax_container_written_path(storage_path)
        storage_dir.cleanup()


@pytest.fixture(scope="module")
def ollama_service() -> None:
    started_mock = False
    if not ollama_container_available():
        start_mock_ollama_container(OLLAMA_CONTAINER)
        started_mock = True
    try:
        yield
    finally:
        if started_mock:
            run_command(["docker", "rm", "-f", OLLAMA_CONTAINER], check=False)


@pytest.fixture(scope="module")
def backend_matrix_image(built_image: str, ollama_service: None) -> str:
    if not ollama_container_available():
        pytest.skip(
            f"Ollama container '{OLLAMA_CONTAINER}' is required for backend tests."
        )
    return built_image


@pytest.mark.parametrize("backend", BACKENDS)
def test_external_backend_matrix_persists_memory_across_restart(
    backend: str, backend_matrix_image: str
) -> None:
    memory_text = f"pytest {backend} memory on Unraid with Postgres"

    with backend_runtime(backend, backend_matrix_image) as runtime:
        wait_http(f"http://127.0.0.1:{runtime['api_port']}/api/v1/config/")
        wait_http(f"http://127.0.0.1:{runtime['ui_port']}/")
        wait_backend_ready(
            backend, str(runtime["backend_container"]), int(runtime["api_port"])
        )

        write_output = http_request(
            f"http://127.0.0.1:{runtime['api_port']}/api/v1/memories/",
            method="POST",
            payload={
                "user_id": "default_user",
                "text": memory_text,
                "metadata": {},
                "infer": False,
                "app": "openmemory",
            },
        )
        assert memory_text in write_output  # nosec B101

        list_output = http_request(
            f"http://127.0.0.1:{runtime['api_port']}/api/v1/memories/?user_id=default_user&page=1&size=20"
        )
        assert memory_text in list_output  # nosec B101

        http_request(
            f"http://127.0.0.1:{runtime['api_port']}{MCP_PATH}",
            method="POST",
            headers={"Accept": "application/json, text/event-stream"},
            payload={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest", "version": "1.0"},
                },
            },
        )
        search_output = http_request(
            f"http://127.0.0.1:{runtime['api_port']}{MCP_PATH}",
            method="POST",
            headers={"Accept": "application/json, text/event-stream"},
            payload={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_memory",
                    "arguments": {"query": f"{backend} Unraid"},
                },
            },
        )
        assert memory_text in search_output  # nosec B101

        run_command(["docker", "restart", str(runtime["mem0_container"])])
        wait_http(f"http://127.0.0.1:{runtime['api_port']}/api/v1/config/")
        restart_output = http_request(
            f"http://127.0.0.1:{runtime['api_port']}/api/v1/memories/?user_id=default_user&page=1&size=20"
        )
        assert memory_text in restart_output  # nosec B101

        logs_result = run_command(
            ["docker", "logs", str(runtime["mem0_container"])], check=False
        )
        logs = logs_result.stdout + logs_result.stderr
        for marker in INVALID_LOG_MARKERS:
            assert marker not in logs  # nosec B101
