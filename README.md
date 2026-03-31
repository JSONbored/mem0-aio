# mem0-aio

Mem0 / OpenMemory packaged as a true All-In-One Unraid container.

`mem0-aio` bundles the OpenMemory API, Next.js UI, and Qdrant into a single container with persistent storage and a beginner-first default setup. The UI is prewired to talk to the API over the same published web port, so a normal Unraid install does not need custom Docker networking or multiple sidecars.

## What This Repo Ships

- A single-container `ghcr.io/jsonbored/mem0-aio:latest` image
- Explicit image tags matching the pinned upstream release, plus `latest` and `sha-...`
- An Unraid CA template at [mem0-aio.xml](/tmp/mem0-aio/mem0-aio.xml)
- A local smoke test at [scripts/smoke-test.sh](/tmp/mem0-aio/scripts/smoke-test.sh)
- Upstream release monitoring via [upstream.toml](/tmp/mem0-aio/upstream.toml) and [scripts/check-upstream.py](/tmp/mem0-aio/scripts/check-upstream.py)
- Automated `awesome-unraid` sync for the XML and icon

## Included Services

- OpenMemory Web UI on port `3000`
- OpenMemory API / MCP server on port `8765`
- Embedded Qdrant vector store on port `6333` inside the container

## Beginner Defaults

- Single published Web UI by default
- Same-origin API proxy so the browser does not need a separate API hostname
- Persistent memory storage in `/mem0/storage`
- Internal Qdrant by default
- Placeholder `OPENAI_API_KEY` fallback so first boot succeeds even before the user chooses a real provider

That fallback is only for startup stability. Real memory generation still needs a valid provider configuration, either through OpenAI-compatible credentials or by switching to a local provider such as Ollama.

## Quick Start

1. Install from the Unraid template.
2. Set `OPENAI_API_KEY` if you want OpenAI as the default provider.
3. If you prefer local inference, leave `OPENAI_API_KEY` blank, start the container, then configure Ollama or another provider from the OpenMemory UI.
4. Open the Web UI and finish provider configuration under settings.

## Power User Notes

- Default browser API traffic uses `/openmemory-api` through the same published UI port.
- You can still publish port `8765` if you want direct MCP/API access from external clients.
- You can override `DATABASE_URL`, `QDRANT_HOST`, `QDRANT_PORT`, `LLM_PROVIDER`, `LLM_MODEL`, `EMBEDDER_PROVIDER`, and related variables for non-default setups.
- See [docs/power-user.md](/tmp/mem0-aio/docs/power-user.md) for the advanced behavior that matters on Unraid.

## Validation

Local validation completed on March 29, 2026:

- native `linux/arm64` Docker build succeeded
- local smoke test passed end-to-end on `linux/arm64`
- explicit `linux/amd64` buildx image build succeeded
- explicit `linux/amd64` smoke test passed end-to-end
- restart and persistence smoke coverage added
- workflow hardening added with pinned action SHAs, dependency review, and upstream release tracking

## Releases

`mem0-aio` uses upstream-version-plus-AIO-revision releases such as `v1.0.9-aio.1`.

Every `main` build publishes `latest`, the exact pinned upstream version, an explicit packaging line tag, and `sha-<commit>`.

See [docs/releases.md](/Users/shadowbook/Documents/mem0-aio/docs/releases.md) for the release workflow details.

## Support

- Issues: [JSONbored/mem0-aio issues](https://github.com/JSONbored/mem0-aio/issues)
- Upstream app: [mem0ai/mem0](https://github.com/mem0ai/mem0)

## Funding

If this work saves you time, support it here:

- [GitHub Sponsors](https://github.com/sponsors/JSONbored)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=JSONbored/mem0-aio&theme=dark)](https://star-history.com/#JSONbored/mem0-aio&Date)
