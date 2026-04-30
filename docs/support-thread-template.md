# Unraid Support Thread Template

Use this as the standard first post for JSONbored AIO Community Apps support threads.

## Required information

- app name
- one-sentence overview
- why this AIO exists
- who it is for
- quick install notes
- first-boot expectations
- persistent paths
- key limitations
- support scope
- project links

## Copy-paste template

Replace all placeholders before posting.

```md
# Support: {{APP_NAME}} ({{SHORT_DESCRIPTOR}} for Unraid)

## What this is

{{APP_NAME}} is {{ONE_SENTENCE_APP_DESCRIPTION}}.

This AIO package exists to make {{UPSTREAM_APP_NAME}} easier to install and maintain on Unraid without forcing users to manually translate a multi-container setup, wire extra dependencies, or guess at first-boot defaults.

## Who this is for

- Beginners who want the easiest reliable Unraid install path
- Intermediate users who want a cleaner AIO baseline
- Power users who still want access to supported advanced settings

## Tradeoffs

- Updates to {{UPSTREAM_APP_NAME}} may lag while the AIO packaging is validated and rebuilt.
- Some advanced upstream configuration paths may not be exposed in the default Unraid template.
- This packaging may behave differently from the official multi-container deployment guide when the AIO wrapper chooses simpler defaults.
- You are relying on the AIO maintainer for packaging fixes, security patches, and catalog refreshes.

## Quick install notes

- Image: `{{IMAGE_NAME}}`
- Default WebUI: `{{WEBUI_URL_OR_NOTE}}`
- Main appdata path: `{{APPDATA_PATHS}}`
- Required setup fields: `{{REQUIRED_FIELDS}}`

### First boot expectations

{{FIRST_BOOT_EXPECTATIONS}}

## Important limitations / caveats

- {{LIMITATION_1}}
- {{LIMITATION_2}}
- {{LIMITATION_3}}

## Persistence

Important persistent paths:

- `{{PATH_1}}`
- `{{PATH_2}}`
- `{{PATH_3}}`

## Support scope

This thread covers the JSONbored Unraid AIO packaging for {{APP_NAME}}.

For support, please include:

- your Unraid version
- your container template settings that matter to the issue
- relevant container logs
- screenshots if the issue is UI-related
- what you expected to happen vs what actually happened

If the issue appears to be upstream behavior rather than the Unraid packaging layer, I may redirect you to the upstream project as appropriate.

## Links

- Project repo: {{PROJECT_REPO_URL}}
- Upstream project: {{UPSTREAM_URL}}
- Catalog repo: {{CATALOG_REPO_URL}}
- Donations:
  - GitHub Sponsors: {{GITHUB_SPONSORS_URL}}
  - Ko-fi: {{KOFI_URL}}

## About the maintainer

Built and maintained by {{MAINTAINER_NAME}} / JSONbored.

- GitHub: {{GITHUB_PROFILE_URL}}
- Portfolio: {{PORTFOLIO_URL}}
```
