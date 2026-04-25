# Changelog

All notable changes to this project will be documented in this file.
## [v2.0.0-aio.3](https://github.com/JSONbored/mem0-aio/releases/tag/v2.0.0-aio.3) - 2026-04-25
### CI
- Optimize pytest gating and Trunk uploads by @JSONbored
- Preserve changelog history and publish release commits by @JSONbored
- Capture integration diagnostics on pytest failure by @JSONbored
- Remove automation flag and align publish flow by @JSONbored
- Centralize trunk config and gate release tags by @JSONbored
- Accept squash release titles by @JSONbored
- Target the release commit on merged PRs by @JSONbored
- Fetch history for release tag lookup by @JSONbored
- Consolidate pytest workflow steps by @JSONbored


### Dependency Updates
- Update trunk-io/analytics-uploader action to v2 by @renovate[bot]
- Update dependency pytest to v9 [security] by @renovate[bot]
- Update ubuntu docker tag to v26 by @renovate[bot]


### Documentation
- Format changelog by @JSONbored


### Fixes
- Make derived repo validator portable by @JSONbored
- Use workflow file selector for CI checks by @JSONbored
- Add authenticated qdrant support by @JSONbored
- Classify local action changes by @JSONbored


### Other Changes
- Merge branch 'main' into codex/ci-diagnostics-fixes by @JSONbored
- Merge branch 'main' into codex/release-target-immutability by @JSONbored
- Harden vector store selection and Unraid template guidance by @JSONbored


### Tests
- Replace smoke tests with pytest by @JSONbored
- Unify validation under pytest by @JSONbored
- Use docker volumes for runtime persistence by @JSONbored
- Require external backend coverage by @JSONbored
- Clean container-owned backend storage by @JSONbored
- Cover action and container contracts by @JSONbored
- Require init fail-fast contract by @JSONbored
- Cover invalid vector store config by @JSONbored


## [v2.0.0-aio.3](https://github.com/JSONbored/mem0-aio/releases/tag/v2.0.0-aio.3) - 2026-04-24

### CI

- Optimize pytest gating and Trunk uploads by @JSONbored
- Preserve changelog history and publish release commits by @JSONbored
- Capture integration diagnostics on pytest failure by @JSONbored
- Remove automation flag and align publish flow by @JSONbored
- Centralize trunk config and gate release tags by @JSONbored
- Accept squash release titles by @JSONbored

### Dependency Updates

- Update trunk-io/analytics-uploader action to v2 by @renovate[bot]
- Update dependency pytest to v9 [security] by @renovate[bot]

### Fixes

- Make derived repo validator portable by @JSONbored
- Use workflow file selector for CI checks by @JSONbored
- Add authenticated qdrant support by @JSONbored

### Other Changes

- Merge branch 'main' into codex/ci-diagnostics-fixes by @JSONbored

### Tests

- Replace smoke tests with pytest by @JSONbored
- Unify validation under pytest by @JSONbored
- Use docker volumes for runtime persistence by @JSONbored
- Require external backend coverage by @JSONbored
- Clean container-owned backend storage by @JSONbored

## [v2.0.0-aio.2](https://github.com/JSONbored/mem0-aio/releases/tag/v2.0.0-aio.2) - 2026-04-18

### Fixes

- Align healthcheck and template auto defaults by @JSONbored
- Align provider auto mode and container healthcheck by @JSONbored
- Point openmemory submodule to maintained fork by @JSONbored

### Other Changes

- Document Ollama and external backend setup by @JSONbored

## [v2.0.0-aio.1](https://github.com/JSONbored/mem0-aio/releases/tag/v2.0.0-aio.1) - 2026-04-17

### Documentation

- Update Socialify banner by @JSONbored

### Features

- Align mem0-aio with OpenMemory v2.0.0 by @JSONbored

### Fixes

- Make releases manual and gate heavy workflows by @JSONbored
- Harden publish and changelog range by @JSONbored

## [v1.0.9-aio.1](https://github.com/JSONbored/mem0-aio/releases/tag/v1.0.9-aio.1) - 2026-04-17

### Dependency Updates

- Update non-major infrastructure updates by @renovate[bot]
- Update node.js to v24 by @renovate[bot]
- Pin ubuntu docker tag to 186072b by @renovate[bot]
- Update docker/build-push-action action to v7 by @renovate[bot]
- Update docker/setup-buildx-action action to v4 by @renovate[bot]
- Update docker/setup-qemu-action action to v4 by @renovate[bot]
- Update docker/metadata-action action to v6 by @renovate[bot]
- Update docker/login-action action to v4 by @renovate[bot]

### Documentation

- Add repository guidance by @JSONbored

### Features

- Initial commit for Mem0 AIO Unraid template with s6-overlay by @JSONbored
- Complete AIO docker build for mem0 openmemory with all s6 hooks and awesome-unraid xml by @JSONbored
- Add git-cliff release workflow by @JSONbored

### Fixes

- Tighten changelog spacing by @JSONbored
- Make releases manual and gate heavy workflows by @JSONbored
- Harden publish and changelog range by @JSONbored

### Maintenance

- Standardize README, add FUNDING.yml, and clean up legacy files by @JSONbored
- Prepare for clean submodule by @JSONbored
- Standardize template by @JSONbored
- Add template sync workflow by @JSONbored
- Revert to verifiable bot identity for non-repudiation by @JSONbored

### Other Changes

- Force rebuild to publish docker image by @JSONbored
- Security & CI: Fix node24 deprecation and package write permissions by @JSONbored
- Link Mem0 as recursive submodule and update CI to include submodules in build by @JSONbored
- Adjust Dockerfile COPY paths to match actual OpenMemory submodule structure by @JSONbored
- Harden mem0-aio and add smoke testing by @JSONbored
- Harden mem0-aio workflows and upstream tracking by @JSONbored
- Add Codex repo memory notes by @JSONbored
- Add renovate.json by @renovate[bot]
- Merge branch 'main' into codex/harden-mem0-aio by @JSONbored
- Reduce smoke-test CI usage by @JSONbored
- Standardize funding and security docs by @JSONbored
- Add standard community templates by @JSONbored
- Consolidate CI workflows by @JSONbored
- Consolidate CI workflows by @JSONbored
- Merge main into consolidate-ci-workflows by @JSONbored
- Merge remote-tracking branch 'origin/main' into codex/reduce-smoke-ci by @JSONbored
- Fix awesome-unraid sync for protected main by @JSONbored
- Standardize upstream-aligned image tags by @JSONbored

### New Contributors

- @JSONbored made their first contribution in [#21](https://github.com/JSONbored/mem0-aio/pull/21)
- @renovate[bot] made their first contribution
<!-- generated by git-cliff -->
