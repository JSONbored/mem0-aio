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
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `OLLAMA_BASE_URL`
- `EMBEDDER_PROVIDER`
- `EMBEDDER_MODEL`
- `EMBEDDER_API_KEY`
- `EMBEDDER_BASE_URL`

Examples:

- OpenAI default:
  - set `OPENAI_API_KEY`
- Local Ollama:
  - set `LLM_PROVIDER=ollama`
  - set `LLM_MODEL=llama3.1:latest`
  - set `EMBEDDER_PROVIDER=ollama`
  - set `EMBEDDER_MODEL=nomic-embed-text`
  - set `OLLAMA_BASE_URL=http://host.docker.internal:11434`

## Storage

- Default persistent path: `/mem0/storage`
- This holds the SQLite database and embedded Qdrant data for the AIO deployment

## External Overrides

These are optional and only for non-default installs:

- `DATABASE_URL`
- `QDRANT_HOST`
- `QDRANT_PORT`

If you override those, you are intentionally stepping outside the normal single-container AIO path.
