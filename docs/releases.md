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
- `sha-<commit>`

Release commits also publish the exact immutable release package tag, for example `v2.0.0-aio.1`. Ordinary `main` pushes do not overwrite that release tag.

When Docker Hub credentials are configured, the same tag set is pushed to Docker Hub in parallel with GHCR.

## Release flow

1. Trigger **Prepare Release / Mem0-AIO** from `main`.
2. The workflow computes the next `upstream-aio.N` version, updates `CHANGELOG.md`, syncs the XML `<Changes>` block, and opens a release PR.
3. Review and merge that PR into `main`.
4. Wait for the `CI / Mem0-AIO` run on the release commit to finish green. That same `main` push also publishes the updated package tags automatically.
5. Trigger **Publish Release / Mem0-AIO** from `main`.
6. The workflow verifies CI on the exact release commit, creates the Git tag if needed, and publishes the GitHub Release.
