# Changelog

## Unreleased

- Added a real local smoke test for `mem0-aio`
- Fixed the broken UI build copy path
- Replaced the broken s6-rc layout with working `cont-init.d` and `services.d` supervision
- Added same-origin UI proxying for easier Unraid installs
- Fixed Qdrant runtime dependencies in the final image
- Added first-boot placeholder handling so the stack can start before a real provider is configured
- Added repo hygiene files, CA template sync improvements, and icon syncing
