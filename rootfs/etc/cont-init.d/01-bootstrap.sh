#!/command/with-contenv bash
set -euo pipefail

mkdir -p /mem0/storage

export USER="${USER:-default_user}"
export NEXT_PUBLIC_USER_ID="${NEXT_PUBLIC_USER_ID:-${USER}}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-/openmemory-api}"
export DATABASE_URL="${DATABASE_URL:-sqlite:////mem0/storage/openmemory.db}"
export QDRANT_HOST="${QDRANT_HOST:-127.0.0.1}"
export QDRANT_PORT="${QDRANT_PORT:-6333}"
export QDRANT__TELEMETRY_DISABLED="${QDRANT__TELEMETRY_DISABLED:-true}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-not-configured}"

cat > /var/run/mem0-aio.env <<EOF
USER="${USER}"
NEXT_PUBLIC_USER_ID="${NEXT_PUBLIC_USER_ID}"
NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}"
DATABASE_URL="${DATABASE_URL}"
QDRANT_HOST="${QDRANT_HOST}"
QDRANT_PORT="${QDRANT_PORT}"
QDRANT__TELEMETRY_DISABLED="${QDRANT__TELEMETRY_DISABLED}"
OPENAI_API_KEY="${OPENAI_API_KEY}"
EOF

chmod 600 /var/run/mem0-aio.env
echo "[mem0-aio] bootstrap complete"
