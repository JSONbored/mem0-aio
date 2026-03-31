# AGENTS.md

This repository is part of a broader portfolio of Unraid-first AIO projects.

## Repository intent

- This repo packages an opinionated, beginner-friendly Unraid AIO deployment.
- Default behavior should optimize for a reliable first boot on Unraid.
- Advanced users should retain escape hatches where supported.

## Engineering expectations

- Prefer consistency with `unraid-aio-template` over one-off repo behavior.
- Keep CI and release behavior aligned with the rest of the AIO fleet.
- Respect protected branches and use PR-based automation for external sync flows.
- Favor operational clarity over cleverness.

## Release model

- Container packages publish automatically from `main`.
- Formal changelog updates and GitHub Releases are release-driven.
- Releases use `upstream version + aio revision`, for example `v1.0.9-aio.1`.
- Keep changelog-friendly Conventional Commit titles and PR titles.

## Unraid expectations

- Unraid-facing XML/icon assets should stay aligned with `awesome-unraid`.
- User-facing metadata should remain accurate:
  - `Project`
  - `Support`
  - `TemplateURL`
  - `Icon`
  - `Overview`
  - `Category`

## Documentation expectations

- Be explicit about operational tradeoffs.
- Do not imply the AIO model removes inherent complexity from the upstream software.
- Keep beginner defaults simple, but document power-user override paths where they exist.
