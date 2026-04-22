# mem0-aio

![mem0-aio](https://socialify.git.ci/JSONbored/mem0-aio/image?custom_description=Unraid+CA+AIO+template+and+Docker+image+for+Mem0+%28OpenMemory%29%2C+an+AI+memory+retention+layer.&custom_language=Dockerfile&description=1&font=Raleway&forks=1&issues=1&language=1&logo=https%3A%2F%2Favatars.githubusercontent.com%2Fu%2F137054526%3Fs%3D200%26v%3D4&name=1&owner=1&pattern=Circuit+Board&pulls=1&stargazers=1&theme=Light)

An Unraid-first, single-container deployment of [Mem0 OpenMemory](https://github.com/mem0ai/mem0/tree/main/openmemory) for people who want the easiest reliable self-hosted install without manually wiring a separate vector database on day one.

`mem0-aio` keeps the critical first-boot dependency bundled: Qdrant plus persistent local storage. The wrapper is opinionated for a predictable beginner install, but it does not hide the real tradeoffs: OpenMemory still needs a valid model/provider configuration to do useful work, external vector backends and hosted model endpoints still need operator knowledge, and exposing the direct MCP/API port is a deliberate security decision rather than a default requirement.

## What This Image Includes

- OpenMemory web UI on port `3000`
- OpenMemory API / MCP server on port `8765`
- Embedded Qdrant vector store
- Persistent appdata storage for SQLite and Qdrant state
- Upstream backup/export helper scripts bundled into the image
- Same-origin UI routing to the API so a standard Unraid install does not need separate browser-facing API networking
- Unraid CA template at [mem0-aio.xml](mem0-aio.xml)

## Beginner Install

If you want the simplest supported path:

1. Install the Unraid template.
2. Leave the default appdata path in place.
3. Either set `OPENAI_API_KEY` for the hosted quick-start, or set `OLLAMA_BASE_URL` to your external native Ollama root URL for the normal local-LLM path.
4. If you use Ollama, also set `LLM_MODEL` and `EMBEDDER_MODEL` to models you already have pulled on that server.
5. Start the container.
6. Open the web UI on port `3000`.
7. If you need something more custom, finish provider configuration in the UI or use the advanced environment overrides.

Leaving `OPENAI_API_KEY` blank is supported. The intended companion path is external Ollama, not bundled inference inside this image.

When `OLLAMA_BASE_URL` is set and you do not explicitly override `LLM_PROVIDER` or `EMBEDDER_PROVIDER`, the wrapper now defaults both to `ollama` automatically.

For normal Ollama installs, the wrapper now also auto-detects the embedding dimension it needs for Qdrant. If you use a custom embedder and auto-detection cannot determine the size, set `EMBEDDER_DIMENSIONS` explicitly in Advanced View.

## Power User Surface

This repo is deliberately not a stripped-down wrapper. The template now tracks the practical OpenMemory self-hosted environment surface exposed by upstream source and docs, plus AIO defaults for the bundled SQLite + Qdrant path. In Advanced View you can:

- point OpenMemory at Ollama, Anthropic, Groq, Together, DeepSeek, Azure OpenAI, Bedrock-compatible providers, and other upstream-supported provider values
- use native Ollama root URLs for the normal homelab path, or OpenAI-compatible `/v1` base URLs for auth-protected reverse proxies
- override both LLM and embedder providers, models, API keys, and base URLs independently
- move vector storage to Chroma, Weaviate, Redis, pgvector, Milvus, Elasticsearch, OpenSearch, or FAISS
- keep using bundled Qdrant privately by default with telemetry disabled unless you explicitly re-enable it
- keep the bundled internal defaults for the easiest install while still exposing the upstream env surface for power users

The wrapper still defaults to the internal bundled storage path so new Unraid users are not forced into extra services on day one.

## Runtime Notes

- As of `2026-04-17`, upstream Mem0 has a newer stable release than the original wrapper baseline; this repo is being moved to the current stable `v2.0.0` line rather than staying on the older `v1.0.x` line.
- The direct API / MCP port is optional for normal browser use because the UI proxies to the API over the same published web port.
- The embedded Qdrant service is intentionally bundled because that is the critical first-boot dependency for the AIO path. External vector store support remains optional advanced configuration.
- Native Ollama provider support expects the root Ollama URL such as `http://host.docker.internal:11434`, not an OpenAI-compatible `/v1` path.
- If your homelab front door adds auth and only exposes an OpenAI-style `/v1` endpoint, use the OpenAI-compatible base URL fields instead of the native Ollama provider path.
- Elasticsearch/OpenSearch support is now wired for real external deployments, but those stacks usually need explicit auth and SSL choices. For Elasticsearch, the advanced template now exposes `ELASTICSEARCH_USE_SSL` and `ELASTICSEARCH_VERIFY_CERTS`. For OpenSearch, it now also exposes optional user/password plus `OPENSEARCH_USE_SSL` and `OPENSEARCH_VERIFY_CERTS`, with SSL defaulting to `true` to match modern secured nodes.
- If you expose OpenMemory beyond your LAN, treat the direct MCP/API surface and your model/provider credentials as real attack surface.

## Publishing and Releases

- Wrapper releases use the upstream version plus an AIO revision, such as `v2.0.0-aio.1`.
- The repo monitors upstream releases through [upstream.toml](upstream.toml) and [scripts/check-upstream.py](scripts/check-upstream.py).
- Release notes are generated with `git-cliff`.
- The Unraid template `<Changes>` block is synced from `CHANGELOG.md` during release preparation.
- `main` publishes `latest`, the pinned upstream version tag, an explicit AIO packaging line tag, and `sha-<commit>`.
- When Docker Hub credentials are configured, the same publish flow pushes Docker Hub tags in parallel with GHCR so the CA template can read Docker Hub metadata.

See [docs/releases.md](docs/releases.md) for the release workflow details.

## Validation

Required local validation is pytest-first:

```bash
git submodule update --init --recursive
python3 -m venv .venv-local
.venv-local/bin/pip install -r requirements-dev.txt
.venv-local/bin/pytest tests/unit tests/template --junit-xml=reports/pytest-unit.xml -o junit_family=xunit1
.venv-local/bin/pytest tests/integration -m integration --junit-xml=reports/pytest-integration.xml -o junit_family=xunit1
trunk flakytests validate --junit-paths "reports/pytest-unit.xml,reports/pytest-integration.xml"
trunk check --show-existing --all
```

The optional external-backend matrix is pytest-based too. It is intentionally opt-in because it requires a prepared Ollama container plus extra sidecar services:

```bash
MEM0_ENABLE_BACKEND_MATRIX=1 \
OLLAMA_CONTAINER=ollama-temp \
.venv-local/bin/pytest tests/integration/test_backend_matrix.py -m extended_integration
```

## Support

- Repo issues: [JSONbored/mem0-aio issues](https://github.com/JSONbored/mem0-aio/issues)
- Upstream app: [mem0ai/mem0](https://github.com/mem0ai/mem0)
- Official OpenMemory docs: [docs.mem0.ai](https://docs.mem0.ai/openmemory/quickstart)

## Funding

If this work saves you time, support it here:

- [GitHub Sponsors](https://github.com/sponsors/JSONbored)
- [Ko-fi](https://ko-fi.com/jsonbored)
- [Buy Me a Coffee](https://buymeacoffee.com/jsonbored)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=JSONbored/mem0-aio&theme=dark)](https://star-history.com/#JSONbored/mem0-aio&Date)
