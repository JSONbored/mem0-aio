# Changelog

All notable changes to this project will be documented in this file.

## v2.0.7-aio.1 - 2026-06-18

### Maintenance

- Bump mem0 to v2.0.7 (#102)

### Refactors

- Migrate to the shared aio-base s6 overlay (#103)

## v2.0.6-aio.1 - 2026-06-17

### Maintenance

- Bump mem0 to v2.0.6 (#100)

## v2.0.5-aio.1 - 2026-06-12

### Maintenance

- Bump mem0 to v2.0.5 (#98)

### Tests

- Use shared app test helpers

## v2.0.4-aio.1 - 2026-05-28

### Maintenance

- Bump mem0 to v2.0.4

## v2.0.2-aio.4 - 2026-05-26

### Documentation

- Normalize CA metadata

## v2.0.2-aio.3 - 2026-05-19

### Fixes

- Harden mem0 apt and upstream provenance

### Maintenance

- Remove repo-local test deps

## v2.0.2-aio.2 - 2026-05-17

### Documentation

- Clarify Mem0 API bind address

## v2.0.2-aio.1 - 2026-05-17

### Maintenance

- Bump mem0 to v2.0.2

## v2.0.1-aio.3 - 2026-05-10

### Fixes

- Restrict mem0 apt sources

### Tests

- Declare mem0 security test dependencies

## v2.0.1-aio.2 - 2026-05-10

### Fixes

- Tighten mem0 runtime defaults
- Satisfy mem0 central trunk policy
- Harden mem0 apt bootstrap retries
- Stabilize mem0 arm64 apt bootstrap
- Preserve signed Ubuntu apt sources

## v2.0.1-aio.1 - 2026-05-05

### Build

- Harden apt package installs

### CI

- Use shared AIO build workflow
- Centralize release workflows
- Repin shared workflow ref
- Centralize workflow drift checks
- Repin caller workflows
- Pin catalog asset manifest
- Pin shared validation policy
- Use shared AIO workflows
- Sync workflow path filters
- Sync catalog publication state
- Pin publish helper workflow fix
- Pin next-wave aio-fleet workflows
- Pin Docker Hub primary workflow
- Pin control-plane workflow foundation

### Documentation

- Document central app test dependencies

### Features

- Expose manual publish targets

### Fixes

- Align mem0 icon sync target
- Sync shared validation and trunk cleanup
- Sync release shim path fallback
- Preserve inherited apt source scheme

### Maintenance

- Sync shared repository boilerplate
- Move shared automation to aio-fleet
- Declare aio-fleet ownership
- Bump mem0 to v2.0.1

### Refactors

- Use shared derived repo validation
- Use shared release helper shim
- Remove legacy shared contract tests

### Tests

- Repin workflow expectation
- Run shared metadata validation

## v2.0.0-aio.3 - 2026-04-25

### CI

- Optimize pytest gating and Trunk uploads
- Preserve changelog history and publish release commits
- Capture integration diagnostics on pytest failure
- Remove automation flag and align publish flow
- Centralize trunk config and gate release tags
- Accept squash release titles
- Target the release commit on merged PRs
- Fetch history for release tag lookup
- Consolidate pytest workflow steps

### Dependency Updates

- Update trunk-io/analytics-uploader action to v2
- Update dependency pytest to v9 [security]
- Update ubuntu docker tag to v26

### Documentation

- Format changelog

### Fixes

- Make derived repo validator portable
- Use workflow file selector for CI checks
- Add authenticated qdrant support
- Classify local action changes

### Other Changes

- Merge branch 'main' into codex/ci-diagnostics-fixes
- Merge branch 'main' into codex/release-target-immutability
- Harden vector store selection and Unraid template guidance

### Tests

- Replace smoke tests with pytest
- Unify validation under pytest
- Use docker volumes for runtime persistence
- Require external backend coverage
- Clean container-owned backend storage
- Cover action and container contracts
- Require init fail-fast contract
- Cover invalid vector store config

## v2.0.0-aio.2 - 2026-04-18

### Fixes

- Align healthcheck and template auto defaults
- Align provider auto mode and container healthcheck
- Point openmemory submodule to maintained fork

### Other Changes

- Document Ollama and external backend setup

## v2.0.0-aio.1 - 2026-04-17

### Documentation

- Update Socialify banner

### Features

- Align mem0-aio with OpenMemory v2.0.0

### Fixes

- Make releases manual and gate heavy workflows
- Harden publish and changelog range

## v1.0.9-aio.1 - 2026-03-31

### Dependency Updates

- Update non-major infrastructure updates
- Update node.js to v24
- Pin ubuntu docker tag to 186072b
- Update docker/build-push-action action to v7
- Update docker/setup-buildx-action action to v4
- Update docker/setup-qemu-action action to v4
- Update docker/metadata-action action to v6
- Update docker/login-action action to v4

### Documentation

- Add repository guidance

### Features

- Initial commit for Mem0 AIO Unraid template with s6-overlay
- Complete AIO docker build for mem0 openmemory with all s6 hooks and awesome-unraid xml
- Add git-cliff release workflow

### Fixes

- Tighten changelog spacing

### Maintenance

- Standardize README, add FUNDING.yml, and clean up legacy files
- Prepare for clean submodule
- Standardize template
- Add template sync workflow
- Revert to verifiable bot identity for non-repudiation

### Other Changes

- Force rebuild to publish docker image
- Security & CI: Fix node24 deprecation and package write permissions
- Link Mem0 as recursive submodule and update CI to include submodules in build
- Adjust Dockerfile COPY paths to match actual OpenMemory submodule structure
- Harden mem0-aio and add smoke testing
- Harden mem0-aio workflows and upstream tracking
- Add Codex repo memory notes
- Add renovate.json
- Merge branch 'main' into codex/harden-mem0-aio
- Reduce smoke-test CI usage
- Standardize funding and security docs
- Add standard community templates
- Consolidate CI workflows
- Consolidate CI workflows
- Merge main into consolidate-ci-workflows
- Merge remote-tracking branch 'origin/main' into codex/reduce-smoke-ci
- Fix awesome-unraid sync for protected main
- Standardize upstream-aligned image tags

<!-- generated by git-cliff -->
