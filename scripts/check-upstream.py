#!/usr/bin/env python3
from __future__ import annotations

import configparser
import json
import os
import pathlib
import re
import subprocess  # nosec B404 - automation shells out only to trusted local git
import sys
import urllib.error
import urllib.request
from typing import NoReturn

ROOT = pathlib.Path(".")
UPSTREAM_FILE = ROOT / "upstream.toml"
DOCKERFILE = ROOT / "Dockerfile"
GIT_BIN = "/usr/bin/git"
SEMVER_RE = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?$"
)


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def http_json(url: str, headers: dict[str, str] | None = None) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json, application/json",
            "User-Agent": "jsonbored-mem0-aio",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
            return json.load(response)
    except urllib.error.HTTPError as exc:
        fail(f"HTTP error while requesting {url}: {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        fail(f"Network error while requesting {url}: {exc.reason}")


def parse_version(value: str) -> tuple[int, int, int, bool, str]:
    match = SEMVER_RE.match(value)
    if not match:
        fail(f"Unsupported version format: {value}")
    prerelease = match.group("prerelease")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease is not None,
        prerelease or "",
    )


def version_sort_key(value: str) -> tuple[int, int, int, int, str]:
    major, minor, patch, is_prerelease, prerelease = parse_version(value)
    return (major, minor, patch, 0 if is_prerelease else 1, prerelease)


def filter_versions(values: list[str], stable_only: bool) -> list[str]:
    semver_values = [value for value in values if SEMVER_RE.match(value)]
    if not stable_only:
        return semver_values
    stable_values: list[str] = []
    for value in semver_values:
        _, _, _, is_prerelease, _ = parse_version(value)
        if not is_prerelease:
            stable_values.append(value)
    return stable_values


def github_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def latest_github_release(repo: str, stable_only: bool) -> str:
    data = http_json(
        f"https://api.github.com/repos/{repo}/releases?per_page=100", github_headers()
    )
    if not isinstance(data, list):
        fail(f"Unexpected GitHub releases response for {repo}")
    releases: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        tag = entry.get("tag_name")
        if not isinstance(tag, str) or not SEMVER_RE.match(tag):
            continue
        prerelease = bool(entry.get("prerelease"))
        if stable_only and prerelease:
            continue
        releases.append(tag)
    if not releases:
        fail(f"No matching releases found for upstream repo {repo}")
    return sorted(releases, key=version_sort_key)[-1]


def read_local_version(config: dict[str, object]) -> str:
    version_source = str(config.get("version_source", "")).strip()
    version_key = str(config.get("version_key", "")).strip()
    if version_source != "dockerfile-arg":
        fail(f"Unsupported version_source: {version_source}")
    pattern = re.compile(rf"^\s*ARG\s+{re.escape(version_key)}=(.+?)\s*$")
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1)
    fail(f"Could not find ARG {version_key} in Dockerfile")


def write_local_version(config: dict[str, object], new_version: str) -> None:
    version_source = str(config.get("version_source", "")).strip()
    version_key = str(config.get("version_key", "")).strip()
    if version_source != "dockerfile-arg":
        fail(f"Unsupported version_source: {version_source}")

    pattern = re.compile(rf"^(\s*ARG\s+{re.escape(version_key)}=).+?(\s*)$")
    updated_lines: list[str] = []
    changed = False
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            updated_lines.append(f"{match.group(1)}{new_version}{match.group(2)}")
            changed = True
        else:
            updated_lines.append(line)
    if not changed:
        fail(f"Could not update ARG {version_key} in Dockerfile")
    DOCKERFILE.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    submodule_path = str(config.get("submodule_path", "")).strip()
    if submodule_path:
        subprocess.run(
            [GIT_BIN, "-C", submodule_path, "fetch", "--tags", "origin"], check=True
        )  # nosec
        subprocess.run(
            [GIT_BIN, "-C", submodule_path, "checkout", new_version], check=True
        )  # nosec


def write_outputs(outputs: dict[str, str]) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            for key, value in outputs.items():
                handle.write(f"{key}={value}\n")
    else:
        for key, value in outputs.items():
            print(f"{key}={value}")


def parse_upstream_toml(path: pathlib.Path) -> dict[str, dict[str, object]]:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read_string(path.read_text(encoding="utf-8"))

    result: dict[str, dict[str, object]] = {}
    for section in parser.sections():
        values: dict[str, object] = {}
        for key, raw_value in parser.items(section):
            value = raw_value.strip()
            lower = value.lower()
            if lower == "true":
                values[key] = True
            elif lower == "false":
                values[key] = False
            else:
                values[key] = value.strip('"')
        result[section] = values
    return result


def main() -> None:
    if not UPSTREAM_FILE.exists():
        fail("Missing upstream.toml")

    config = parse_upstream_toml(UPSTREAM_FILE)
    upstream = config.get("upstream")
    notifications = config.get("notifications", {})
    if not isinstance(upstream, dict):
        fail("Invalid upstream.toml: missing [upstream]")

    upstream_type = str(upstream.get("type", "")).strip()
    stable_only = bool(upstream.get("stable_only", True))
    current_version = read_local_version(upstream)

    if upstream_type == "github-release":
        latest_version = latest_github_release(
            str(upstream.get("repo", "")).strip(), stable_only
        )
    else:
        fail(f"Unsupported upstream type: {upstream_type}")

    updates_available = latest_version != current_version

    if os.environ.get("WRITE_UPSTREAM_VERSION") == "true" and updates_available:
        write_local_version(upstream, latest_version)

    release_notes = ""
    if isinstance(notifications, dict):
        release_notes = str(notifications.get("release_notes_url", "")).strip()
    if not release_notes and upstream.get("repo"):
        release_notes = f"https://github.com/{upstream['repo']}/releases"

    write_outputs(
        {
            "current_version": current_version,
            "latest_version": latest_version,
            "updates_available": "true" if updates_available else "false",
            "strategy": str(upstream.get("strategy", "pr")).strip() or "pr",
            "upstream_name": str(upstream.get("name", "")).strip(),
            "release_notes_url": release_notes,
        }
    )


if __name__ == "__main__":
    main()
