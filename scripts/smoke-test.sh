#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-mem0-aio:test}"
CONTAINER_NAME="${CONTAINER_NAME:-mem0-aio-smoke}"
HOST_UI_PORT="${HOST_UI_PORT:-43000}"
HOST_API_PORT="${HOST_API_PORT:-48765}"
HOST_QDRANT_PORT="${HOST_QDRANT_PORT:-46333}"
READY_TIMEOUT_SECONDS="${READY_TIMEOUT_SECONDS:-240}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-2}"
KEEP_SMOKE_ARTIFACTS="${KEEP_SMOKE_ARTIFACTS:-0}"
TMP_STORAGE="$(mktemp -d /tmp/mem0-aio-storage.XXXXXX)"

cleanup() {
    if [ "${KEEP_SMOKE_ARTIFACTS}" = "1" ]; then
        echo "Smoke test artifacts preserved for debugging."
        echo "SMOKE_CONTAINER_NAME=${CONTAINER_NAME}"
        echo "SMOKE_STORAGE_DIR=${TMP_STORAGE}"
        return
    fi

    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    rm -rf "${TMP_STORAGE}"
}
trap cleanup EXIT

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_UI_PORT}:3000" \
    -p "${HOST_API_PORT}:8765" \
    -p "${HOST_QDRANT_PORT}:6333" \
    -v "${TMP_STORAGE}:/mem0/storage" \
    "${IMAGE_TAG}" >/dev/null

dump_failure_state() {
    echo "Smoke test failed for ${IMAGE_TAG}" >&2
    echo "--- docker ps ---" >&2
    docker ps -a >&2 || true
    echo "--- container logs ---" >&2
    docker logs "${CONTAINER_NAME}" >&2 || true
}

wait_for_ready() {
    local attempts
    local container_status
    attempts=$(( READY_TIMEOUT_SECONDS / POLL_INTERVAL_SECONDS ))
    for _ in $(seq 1 "${attempts}"); do
        if curl -fsS "http://127.0.0.1:${HOST_UI_PORT}/" >/dev/null 2>&1 && \
           curl -fsS "http://127.0.0.1:${HOST_API_PORT}/api/v1/config/" >/dev/null 2>&1 && \
           curl -fsS "http://127.0.0.1:${HOST_QDRANT_PORT}/readyz" >/dev/null 2>&1; then
            return 0
        fi

        container_status="$(docker inspect -f '{{.State.Status}}' "${CONTAINER_NAME}" 2>/dev/null || true)"
        if [ -z "${container_status}" ] || [ "${container_status}" = "exited" ] || [ "${container_status}" = "dead" ]; then
            echo "Smoke test container exited unexpectedly." >&2
            dump_failure_state
            exit 1
        fi
        sleep "${POLL_INTERVAL_SECONDS}"
    done

    echo "Timed out waiting for mem0-aio services to become ready." >&2
    dump_failure_state
    exit 1
}

verify_runtime() {
    if curl -fsS "http://127.0.0.1:${HOST_UI_PORT}/" >/dev/null 2>&1 && \
       curl -fsS "http://127.0.0.1:${HOST_API_PORT}/api/v1/config/" >/dev/null 2>&1 && \
       curl -fsS "http://127.0.0.1:${HOST_QDRANT_PORT}/readyz" >/dev/null 2>&1; then
        :
    fi
    curl -fsS "http://127.0.0.1:${HOST_UI_PORT}/" >/dev/null
    curl -fsS "http://127.0.0.1:${HOST_API_PORT}/api/v1/config/" >/dev/null
    curl -fsS "http://127.0.0.1:${HOST_UI_PORT}/openmemory-api/api/v1/config" >/dev/null
    curl -fsS "http://127.0.0.1:${HOST_QDRANT_PORT}/readyz" >/dev/null

    if ! docker exec "${CONTAINER_NAME}" sh -lc 'test -f /mem0/storage/openmemory.db'; then
        dump_failure_state
        exit 1
    fi
}

wait_for_ready
verify_runtime

docker restart "${CONTAINER_NAME}" >/dev/null
wait_for_ready
verify_runtime
