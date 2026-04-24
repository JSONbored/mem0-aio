# Power User Notes

`mem0-aio` is designed to boot cleanly as a single container first, then let you override pieces only if you really want to.

## Networking

- The Web UI is the primary published port.
- The UI talks to the API through `/openmemory-api` by default.
- Publish `8765` only if you want direct API or MCP access from external clients.

## Provider Configuration

There are two ways to configure providers:

- through the OpenMemory settings UI, which writes config into the app database
- through container environment variables, which influence auto-detection and first-run defaults

Useful variables:

- `OPENAI_API_KEY`
- `API_KEY` (legacy alias for older `env:API_KEY` examples)
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `OLLAMA_BASE_URL`
- `OLLAMA_HOST`
- `EMBEDDER_PROVIDER`
- `EMBEDDER_MODEL`
- `EMBEDDER_API_KEY`
- `EMBEDDER_BASE_URL`
- `EMBEDDER_DIMENSIONS`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_USER_ID`

Examples:

- OpenAI default:
  - set `OPENAI_API_KEY`
- Local Ollama:
  - set `OLLAMA_BASE_URL=http://host.docker.internal:11434`
  - set `LLM_MODEL` to a chat model you already have pulled
  - set `EMBEDDER_MODEL=nomic-embed-text` or another embedding model you already have pulled
  - usually leave `EMBEDDER_DIMENSIONS` unset so the wrapper can auto-detect it; only set it if your embedder is custom or probing is unavailable
  - leave `LLM_PROVIDER` and `EMBEDDER_PROVIDER` unset unless you want to override the wrapper's automatic Ollama defaulting
- Auth-protected OpenAI-compatible Ollama proxy:
  - set `LLM_PROVIDER=openai`
  - set `EMBEDDER_PROVIDER=openai`
  - set `LLM_BASE_URL=https://your-proxy.example/v1`
  - set `EMBEDDER_BASE_URL=https://your-proxy.example/v1`
  - set `LLM_API_KEY` and `EMBEDDER_API_KEY` if your proxy requires auth

Notes:

- Native Ollama provider support uses the root Ollama API URL, not a `/v1` path.
- The native Ollama path in the upstream Mem0 client does not currently expose custom auth headers. If your reverse proxy requires auth, prefer the OpenAI-compatible base URL path instead.

## Storage

- Default persistent path: `/mem0/storage`
- This holds the SQLite database and embedded Qdrant data for the AIO deployment

## External Overrides

These are optional and only for non-default installs:

- `DATABASE_URL`
- `QDRANT__TELEMETRY_DISABLED`
- `QDRANT_URL`
- `QDRANT_HOST`
- `QDRANT_PORT`
- `QDRANT_API_KEY`
- `CHROMA_HOST` / `CHROMA_PORT`
- `WEAVIATE_CLUSTER_URL` or `WEAVIATE_HOST` / `WEAVIATE_PORT`
- `REDIS_URL`
- `PG_HOST` / `PG_PORT` / `PG_DB` / `PG_USER` / `PG_PASSWORD`
- `MILVUS_HOST` / `MILVUS_PORT` / `MILVUS_TOKEN` / `MILVUS_DB_NAME`
- `ELASTICSEARCH_HOST` / `ELASTICSEARCH_PORT` / `ELASTICSEARCH_USER` / `ELASTICSEARCH_PASSWORD` / `ELASTICSEARCH_USE_SSL` / `ELASTICSEARCH_VERIFY_CERTS`
- `OPENSEARCH_HOST` / `OPENSEARCH_PORT` / `OPENSEARCH_USER` / `OPENSEARCH_PASSWORD` / `OPENSEARCH_USE_SSL` / `OPENSEARCH_VERIFY_CERTS`
- `FAISS_PATH`

## Export Helper

The image now carries upstream's `backup-scripts/export_openmemory.sh` helper under `/app/backup-scripts/export_openmemory.sh`.

Optional expert-only export filter env vars:

- `EXPORT_USER_ID`
- `EXPORT_APP_ID`
- `EXPORT_FROM_DATE`
- `EXPORT_TO_DATE`

If you override those, you are intentionally stepping outside the normal single-container AIO path.

## Authenticated External Qdrant

For an external Qdrant container without auth, `QDRANT_HOST=qdrant` and `QDRANT_PORT=6333` are enough.

For authenticated Qdrant, set:

- `QDRANT_URL=http://qdrant:6333` for a plain HTTP Docker-network endpoint, or an HTTPS URL for a TLS endpoint
- `QDRANT_API_KEY` to the Qdrant API key

Do not rely on `QDRANT_HOST` + `QDRANT_PORT` alone for authenticated plain-HTTP Qdrant. The wrapper normalizes this case for compatibility, but `QDRANT_URL` is the explicit and least surprising configuration.
