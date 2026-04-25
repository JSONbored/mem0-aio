from __future__ import annotations

import subprocess  # nosec B404 - tests execute trusted local helper scripts

from tests.conftest import REPO_ROOT

ENV_HELPERS = REPO_ROOT / "rootfs/etc/mem0-aio/env-helpers.sh"


def run_vector_helper(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    command = (
        f"source {ENV_HELPERS}; "
        "mem0_validate_vector_store_config && "
        "if mem0_uses_external_vector_store; then echo external; else echo bundled; fi"
    )
    return subprocess.run(  # nosec B603 - trusted local bash validation helper
        ["/bin/bash", "-lc", command],
        check=False,
        env=env,
        text=True,
        capture_output=True,
    )


def test_default_qdrant_uses_bundled_vector_store() -> None:
    result = run_vector_helper({"QDRANT_HOST": "127.0.0.1", "QDRANT_PORT": "6333"})

    assert result.returncode == 0  # nosec B101
    assert result.stdout.strip() == "bundled"  # nosec B101


def test_redis_pgvector_and_external_qdrant_are_rejected_together() -> None:
    result = run_vector_helper(
        {
            "REDIS_URL": "redis://redis:6379/0",
            "PG_HOST": "postgres",
            "PG_PORT": "5432",
            "QDRANT_URL": "http://qdrant:6333",
        }
    )

    assert result.returncode == 1  # nosec B101
    assert "choose exactly one vector store backend" in result.stderr  # nosec B101
    assert "redis pgvector qdrant" in result.stderr  # nosec B101


def test_pgvector_partial_config_is_rejected() -> None:
    result = run_vector_helper({"PG_HOST": "postgres"})

    assert result.returncode == 1  # nosec B101
    assert (
        "PGVector requires at least PG_HOST and PG_PORT" in result.stderr
    )  # nosec B101


def test_qdrant_api_key_requires_external_endpoint() -> None:
    result = run_vector_helper(
        {
            "QDRANT_HOST": "127.0.0.1",
            "QDRANT_PORT": "6333",
            "QDRANT_API_KEY": "secret",
        }
    )

    assert result.returncode == 1  # nosec B101
    assert (
        "QDRANT_API_KEY requires QDRANT_URL or an external QDRANT_HOST" in result.stderr
    )  # nosec B101


def test_external_qdrant_host_disables_bundled_store() -> None:
    result = run_vector_helper({"QDRANT_HOST": "qdrant", "QDRANT_PORT": "6333"})

    assert result.returncode == 0  # nosec B101
    assert result.stdout.strip() == "external"  # nosec B101
