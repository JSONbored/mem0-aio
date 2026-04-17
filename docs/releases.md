# Releases

`mem0-aio` uses upstream-version-plus-AIO-revision releases such as `v2.0.0-aio.1`.

## Version format

- first wrapper release for upstream `v2.0.0`: `v2.0.0-aio.1`
- second wrapper-only release on the same upstream: `v2.0.0-aio.2`
- first wrapper release after upgrading upstream again: `vX.Y.Z-aio.1`

## Published image tags

Every `main` build publishes:

- `latest`
- the exact pinned upstream version
- the exact release package tag like `v2.0.0-aio.1`
- `sha-<commit>`

When Docker Hub credentials are configured, the same tag set is pushed to Docker Hub in parallel with GHCR.

## Release flow

1. Trigger **Release / Mem0-AIO** from `main` with `action=prepare`.
2. The workflow computes the next `upstream-aio.N` version and opens a release PR.
3. Review and merge that PR into `main`.
4. Trigger **Release / Mem0-AIO** from `main` again with `action=publish`.
5. The workflow reads the merged `CHANGELOG.md` entry, syncs image publishing via **CI / Mem0-AIO**, creates the Git tag, and publishes the GitHub Release.
