# mem0-aio Agent Notes

`mem0-aio` packages OpenMemory / Mem0 as a single Unraid container with an embedded Qdrant vector store.

## Runtime Shape

- OpenMemory web UI
- OpenMemory API / MCP service
- Internal Qdrant for vector storage
- Same-origin UI-to-API default flow for simple Unraid installs

## Important Behavior

- The vendored `openmemory` submodule is part of the upstream tracking story here.
- `upstream.toml` uses `submodule_path = "openmemory"`.
- Beginner installs should work with internal Qdrant by default.
- A placeholder `OPENAI_API_KEY` fallback exists only to keep startup stable; real memory generation still needs a valid provider.

## CI And Publish Policy

- Validation and smoke tests should run on PRs and branch pushes.
- Publish should happen only from the default branch.
- GHCR image naming must stay lowercase.

## What To Preserve

- Keep the browser experience single-origin by default.
- Keep Qdrant internal unless a user explicitly overrides storage strategy.
- Smoke tests should validate restart and persistence, not just the first boot.
