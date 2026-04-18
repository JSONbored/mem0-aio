#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-mem0-aio:matrix-test}"
BACKEND="${2:-qdrant}"
OLLAMA_CONTAINER="${OLLAMA_CONTAINER:-ollama-temp}"
MEMORY_TEXT="${MEMORY_TEXT:-backend smoke ${BACKEND} memory on Unraid with Postgres}"
HOST_UI_PORT="${HOST_UI_PORT:-$((33000 + RANDOM % 1000))}"
HOST_API_PORT="${HOST_API_PORT:-$((38000 + RANDOM % 1000))}"
NETWORK="mem0-smoke-${BACKEND}-$$"
MEM0_CONTAINER="mem0-smoke-${BACKEND}-$$"
BACKEND_CONTAINER="mem0-backend-${BACKEND}-$$"
TMP_STORAGE="$(mktemp -d "/tmp/mem0-${BACKEND}.XXXXXX")"
FAISS_PATH_IN_CONTAINER="/mem0/storage/faiss"

cleanup() {
    docker rm -f "${MEM0_CONTAINER}" >/dev/null 2>&1 || true
    docker rm -f "${BACKEND_CONTAINER}" >/dev/null 2>&1 || true
    docker network disconnect "${NETWORK}" "${OLLAMA_CONTAINER}" >/dev/null 2>&1 || true
    docker network rm "${NETWORK}" >/dev/null 2>&1 || true
    rm -rf "${TMP_STORAGE}"
}
trap cleanup EXIT

fail() {
    echo "Backend smoke failed for ${BACKEND}" >&2
    echo "--- mem0 logs ---" >&2
    docker logs "${MEM0_CONTAINER}" >&2 || true
    if docker inspect "${BACKEND_CONTAINER}" >/dev/null 2>&1; then
        echo "--- backend logs ---" >&2
        docker logs "${BACKEND_CONTAINER}" >&2 || true
    fi
    exit 1
}

python_json() {
    local url="$1"
    local method="${2:-GET}"
    local payload="${3:-}"
    URL="${url}" METHOD="${method}" PAYLOAD="${payload}" python3 - <<'PY'
import json
import os
import urllib.request

url = os.environ["URL"]
method = os.environ["METHOD"]
payload = os.environ["PAYLOAD"]
headers = {"Content-Type": "application/json"}
data = payload.encode() if payload else None
req = urllib.request.Request(url, data=data, headers=headers, method=method)
with urllib.request.urlopen(req, timeout=30) as resp:
    body = resp.read().decode()
    print(resp.status)
    print(body)
PY
}

python_mcp_call() {
    local payload="$1"
    PAYLOAD="${payload}" HOST_API_PORT="${HOST_API_PORT}" python3 - <<'PY'
import json
import os
import urllib.request

payload = json.loads(os.environ["PAYLOAD"])
req = urllib.request.Request(
    f"http://127.0.0.1:{os.environ['HOST_API_PORT']}/mcp/openmemory/http/default_user",
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    },
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as resp:
    print(resp.status)
    print(resp.read().decode())
PY
}

require_ollama() {
    if ! docker inspect "${OLLAMA_CONTAINER}" >/dev/null 2>&1; then
        echo "Expected Ollama container '${OLLAMA_CONTAINER}' to already be running." >&2
        exit 1
    fi
}

wait_http() {
    local url="$1"
    for _ in $(seq 1 60); do
        if curl -fsS "${url}" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

wait_backend() {
    case "${BACKEND}" in
        qdrant|faiss)
            return 0
            ;;
        chroma)
            for _ in $(seq 1 60); do
                if wait_http "http://127.0.0.1:${HOST_API_PORT}/api/v1/config/"; then
                    return 0
                fi
                sleep 1
            done
            return 1
            ;;
        redis)
            for _ in $(seq 1 60); do
                if docker exec "${BACKEND_CONTAINER}" redis-cli ping | grep -q PONG; then
                    return 0
                fi
                sleep 1
            done
            return 1
            ;;
        pgvector)
            for _ in $(seq 1 60); do
                if docker exec "${BACKEND_CONTAINER}" pg_isready -U mem0 -d mem0; then
                    return 0
                fi
                sleep 1
            done
            return 1
            ;;
        weaviate)
            for _ in $(seq 1 60); do
                if docker exec "${BACKEND_CONTAINER}" wget -qO- http://127.0.0.1:8080/v1/.well-known/ready >/dev/null 2>&1; then
                    return 0
                fi
                sleep 1
            done
            return 1
            ;;
        elasticsearch)
            for _ in $(seq 1 90); do
                if docker exec "${BACKEND_CONTAINER}" curl -fsSk -u elastic:changeme https://127.0.0.1:9200/_cluster/health >/dev/null 2>&1; then
                    return 0
                fi
                sleep 1
            done
            return 1
            ;;
        opensearch)
            for _ in $(seq 1 90); do
                if docker exec "${BACKEND_CONTAINER}" curl -fsSk -u admin:Str0ngP@ssw0rd! https://127.0.0.1:9200/_cluster/health >/dev/null 2>&1; then
                    return 0
                fi
                sleep 1
            done
            return 1
            ;;
        *)
            echo "Unsupported backend '${BACKEND}'" >&2
            return 1
            ;;
    esac
}

start_backend() {
    mkdir -p "${TMP_STORAGE}/faiss"
    docker network create "${NETWORK}" >/dev/null
    docker network connect "${NETWORK}" "${OLLAMA_CONTAINER}" >/dev/null 2>&1 || true

    case "${BACKEND}" in
        qdrant)
            ;;
        faiss)
            ;;
        chroma)
            docker run -d --name "${BACKEND_CONTAINER}" --network "${NETWORK}" \
                chromadb/chroma:0.6.3 >/dev/null
            ;;
        redis)
            docker run -d --name "${BACKEND_CONTAINER}" --network "${NETWORK}" \
                redis/redis-stack-server:latest >/dev/null
            ;;
        pgvector)
            docker run -d --name "${BACKEND_CONTAINER}" --network "${NETWORK}" \
                -e POSTGRES_DB=mem0 \
                -e POSTGRES_USER=mem0 \
                -e POSTGRES_PASSWORD=mem0 \
                pgvector/pgvector:pg17 >/dev/null
            ;;
        weaviate)
            docker run -d --name "${BACKEND_CONTAINER}" --network "${NETWORK}" \
                -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
                -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
                -e QUERY_DEFAULTS_LIMIT=20 \
                -e DEFAULT_VECTORIZER_MODULE=none \
                -e ENABLE_MODULES= \
                semitechnologies/weaviate:1.27.12 >/dev/null
            ;;
        elasticsearch)
            docker run -d --name "${BACKEND_CONTAINER}" --network "${NETWORK}" \
                -e discovery.type=single-node \
                -e ELASTIC_PASSWORD=changeme \
                -e ES_JAVA_OPTS="-Xms512m -Xmx512m" \
                docker.elastic.co/elasticsearch/elasticsearch:8.15.0 >/dev/null
            ;;
        opensearch)
            docker run -d --name "${BACKEND_CONTAINER}" --network "${NETWORK}" \
                -e discovery.type=single-node \
                -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=Str0ngP@ssw0rd! \
                -e OPENSEARCH_JAVA_OPTS="-Xms512m -Xmx512m" \
                opensearchproject/opensearch:2.18.0 >/dev/null
            ;;
        *)
            echo "Unsupported backend '${BACKEND}'" >&2
            exit 1
            ;;
    esac
}

run_mem0() {
    local -a env_args
    env_args=(
        -e OLLAMA_BASE_URL="http://${OLLAMA_CONTAINER}:11434"
        -e LLM_MODEL=tinyllama:latest
        -e EMBEDDER_MODEL=nomic-embed-text:latest
    )

    case "${BACKEND}" in
        qdrant)
            ;;
        faiss)
            env_args+=(-e FAISS_PATH="${FAISS_PATH_IN_CONTAINER}")
            ;;
        chroma)
            env_args+=(-e CHROMA_HOST="${BACKEND_CONTAINER}" -e CHROMA_PORT=8000)
            ;;
        redis)
            env_args+=(-e REDIS_URL="redis://${BACKEND_CONTAINER}:6379/0")
            ;;
        pgvector)
            env_args+=(
                -e PG_HOST="${BACKEND_CONTAINER}"
                -e PG_PORT=5432
                -e PG_DB=mem0
                -e PG_USER=mem0
                -e PG_PASSWORD=mem0
            )
            ;;
        weaviate)
            env_args+=(-e WEAVIATE_HOST="${BACKEND_CONTAINER}" -e WEAVIATE_PORT=8080)
            ;;
        elasticsearch)
            env_args+=(
                -e ELASTICSEARCH_HOST="${BACKEND_CONTAINER}"
                -e ELASTICSEARCH_PORT=9200
                -e ELASTICSEARCH_USER=elastic
                -e ELASTICSEARCH_PASSWORD=changeme
            )
            ;;
        opensearch)
            env_args+=(
                -e OPENSEARCH_HOST="${BACKEND_CONTAINER}"
                -e OPENSEARCH_PORT=9200
                -e OPENSEARCH_USER=admin
                -e OPENSEARCH_PASSWORD=Str0ngP@ssw0rd!
            )
            ;;
    esac

    docker run -d --name "${MEM0_CONTAINER}" --network "${NETWORK}" \
        -p "${HOST_UI_PORT}:3000" -p "${HOST_API_PORT}:8765" \
        -v "${TMP_STORAGE}:/mem0/storage" \
        "${env_args[@]}" \
        "${IMAGE_TAG}" >/dev/null
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    if [[ "${haystack}" != *"${needle}"* ]]; then
        echo "Expected output to contain: ${needle}" >&2
        echo "${haystack}" >&2
        fail
    fi
}

main() {
    require_ollama
    start_backend
    run_mem0

    wait_http "http://127.0.0.1:${HOST_API_PORT}/api/v1/config/" || fail
    wait_http "http://127.0.0.1:${HOST_UI_PORT}/" || fail
    wait_backend || fail

    python_json \
        "http://127.0.0.1:${HOST_API_PORT}/api/v1/memories/" \
        POST \
        "{\"user_id\":\"default_user\",\"text\":\"${MEMORY_TEXT}\",\"metadata\":{},\"infer\":false,\"app\":\"openmemory\"}" \
        >/tmp/mem0-write.out || fail
    write_output="$(cat /tmp/mem0-write.out)"
    assert_contains "${write_output}" "${MEMORY_TEXT}"

    python_json "http://127.0.0.1:${HOST_API_PORT}/api/v1/memories/?user_id=default_user&page=1&size=20" \
        >/tmp/mem0-list.out || fail
    list_output="$(cat /tmp/mem0-list.out)"
    assert_contains "${list_output}" "${MEMORY_TEXT}"

    python_mcp_call '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}' \
        >/tmp/mem0-mcp-init.out || fail
    python_mcp_call "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"search_memory\",\"arguments\":{\"query\":\"${BACKEND} Unraid\"}}}" \
        >/tmp/mem0-mcp-search.out || fail
    search_output="$(cat /tmp/mem0-mcp-search.out)"
    assert_contains "${search_output}" "${MEMORY_TEXT}"

    docker restart "${MEM0_CONTAINER}" >/dev/null || fail
    wait_http "http://127.0.0.1:${HOST_API_PORT}/api/v1/config/" || fail
    python_json "http://127.0.0.1:${HOST_API_PORT}/api/v1/memories/?user_id=default_user&page=1&size=20" \
        >/tmp/mem0-list-restart.out || fail
    restart_output="$(cat /tmp/mem0-list-restart.out)"
    assert_contains "${restart_output}" "${MEMORY_TEXT}"

    logs="$(docker logs "${MEM0_CONTAINER}" 2>&1 || true)"
    if [[ "${logs}" == *"Wrong input: Vector dimension error"* ]] || \
       [[ "${logs}" == *"You didn't provide an API key"* ]] || \
       [[ "${logs}" == *"Error categorizing memory"* ]]; then
        echo "${logs}" >&2
        fail
    fi

    echo "PASS ${BACKEND}"
}

main "$@"
