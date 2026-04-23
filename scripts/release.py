#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess  # nosec - release helpers shell out only to trusted local git

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CHANGELOG = ROOT / "CHANGELOG.md"
DEFAULT_DOCKERFILE = ROOT / "Dockerfile"
DEFAULT_UPSTREAM = ROOT / "upstream.toml"
AIO_TAG_PATTERN = "*-aio.*"
GIT_BIN = "/usr/bin/git"


def git_output(*args: str) -> str:
    return subprocess.check_output([GIT_BIN, *args], cwd=ROOT, text=True)  # nosec


def git_completed(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [GIT_BIN, *args], cwd=ROOT, text=True, capture_output=True, check=False
    )  # nosec


def load_upstream_version_key(path: pathlib.Path) -> str:
    in_upstream = False
    pattern = re.compile(r'^version_key\s*=\s*"([^"]+)"\s*$')
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_upstream = line == "[upstream]"
            continue
        if not in_upstream:
            continue
        match = pattern.match(line)
        if match:
            return match.group(1)
    return "UPSTREAM_VERSION"


def read_upstream_version(dockerfile: pathlib.Path, upstream: pathlib.Path) -> str:
    version_key = load_upstream_version_key(upstream)
    pattern = re.compile(rf"^ARG {re.escape(version_key)}=(.+)$")
    for line in dockerfile.read_text().splitlines():
        match = pattern.match(line.strip())
        if match:
            return match.group(1).split("@", 1)[0]
    raise SystemExit(f"Unable to find ARG {version_key} in {dockerfile}")


def git_tags() -> list[str]:
    output = git_output("tag", "--list")
    return [line.strip() for line in output.splitlines() if line.strip()]


def latest_aio_release_tag() -> str | None:
    completed = git_completed(
        "describe", "--tags", "--abbrev=0", "--match", AIO_TAG_PATTERN, "HEAD"
    )
    if completed.returncode != 0:
        return None
    tag = completed.stdout.strip()
    return tag or None


def latest_release_tag(dockerfile: pathlib.Path, upstream: pathlib.Path) -> str | None:
    upstream_version = read_upstream_version(dockerfile, upstream)
    pattern = re.compile(rf"^{re.escape(upstream_version)}-aio\.(\d+)$")
    matches: list[tuple[int, str]] = []
    for tag in git_tags():
        match = pattern.match(tag)
        if match:
            matches.append((int(match.group(1)), tag))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    return matches[-1][1]


def has_unreleased_changes(dockerfile: pathlib.Path, upstream: pathlib.Path) -> bool:
    latest_tag = latest_aio_release_tag()
    if latest_tag is None:
        return True
    output = git_output("log", "--format=%s", f"{latest_tag}..HEAD")
    return any(line.strip() for line in output.splitlines())


def next_release_version(dockerfile: pathlib.Path, upstream: pathlib.Path) -> str:
    upstream_version = read_upstream_version(dockerfile, upstream)
    pattern = re.compile(rf"^{re.escape(upstream_version)}-aio\.(\d+)$")
    revisions = []
    for tag in git_tags():
        match = pattern.match(tag)
        if match:
            revisions.append(int(match.group(1)))
    next_revision = max(revisions, default=0) + 1
    return f"{upstream_version}-aio.{next_revision}"


def latest_changelog_version(changelog: pathlib.Path) -> str:
    pattern = re.compile(r"^##\s+(?:\[([^\]]+)\]\([^)]+\)|([^\s]+))")
    for line in changelog.read_text().splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        version = match.group(1) or match.group(2)
        if version != "Unreleased":
            return version
    raise SystemExit(f"Unable to find a released version heading in {changelog}")


def extract_release_notes(version: str, changelog: pathlib.Path) -> str:
    heading = re.compile(
        rf"^##\s+(?:\[{re.escape(version)}\]\([^)]+\)|{re.escape(version)})(?:\s+-\s+.+)?$"
    )
    next_heading = re.compile(r"^##\s+")
    lines = changelog.read_text().splitlines()
    start = None
    for index, line in enumerate(lines):
        if heading.match(line.strip()):
            start = index + 1
            break
    if start is None:
        raise SystemExit(f"Unable to find release section for {version} in {changelog}")
    end = len(lines)
    for index in range(start, len(lines)):
        if next_heading.match(lines[index].strip()):
            end = index
            break
    notes = "\n".join(lines[start:end]).strip()
    if not notes:
        raise SystemExit(f"Release section for {version} in {changelog} is empty")
    return notes


def find_release_commit(version: str) -> str:
    exact = f"chore(release): {version}"
    with_suffix = re.compile(rf"^{re.escape(exact)} \(#\d+\)$")

    output = git_output("log", "--format=%H\t%s", "HEAD")
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        if subject == exact or with_suffix.match(subject):
            return sha

    raise SystemExit(
        f"Unable to find a merged release commit for {version} on main. "
        f"Expected '{exact}' or '{exact} (#123)'."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Release helpers for AIO repos.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    upstream_parser = subparsers.add_parser("upstream-version")
    upstream_parser.add_argument(
        "--dockerfile", type=pathlib.Path, default=DEFAULT_DOCKERFILE
    )
    upstream_parser.add_argument(
        "--upstream-config", type=pathlib.Path, default=DEFAULT_UPSTREAM
    )
    next_parser = subparsers.add_parser("next-version")
    next_parser.add_argument(
        "--dockerfile", type=pathlib.Path, default=DEFAULT_DOCKERFILE
    )
    next_parser.add_argument(
        "--upstream-config", type=pathlib.Path, default=DEFAULT_UPSTREAM
    )
    changes_parser = subparsers.add_parser("has-unreleased-changes")
    changes_parser.add_argument(
        "--dockerfile", type=pathlib.Path, default=DEFAULT_DOCKERFILE
    )
    changes_parser.add_argument(
        "--upstream-config", type=pathlib.Path, default=DEFAULT_UPSTREAM
    )
    subparsers.add_parser("latest-aio-tag")
    latest_parser = subparsers.add_parser("latest-changelog-version")
    latest_parser.add_argument(
        "--changelog", type=pathlib.Path, default=DEFAULT_CHANGELOG
    )
    notes_parser = subparsers.add_parser("extract-release-notes")
    notes_parser.add_argument("version")
    notes_parser.add_argument(
        "--changelog", type=pathlib.Path, default=DEFAULT_CHANGELOG
    )
    commit_parser = subparsers.add_parser("find-release-commit")
    commit_parser.add_argument("version")
    args = parser.parse_args()
    if args.command == "upstream-version":
        print(read_upstream_version(args.dockerfile, args.upstream_config))
    elif args.command == "next-version":
        print(next_release_version(args.dockerfile, args.upstream_config))
    elif args.command == "has-unreleased-changes":
        print(
            "true"
            if has_unreleased_changes(args.dockerfile, args.upstream_config)
            else "false"
        )
    elif args.command == "latest-aio-tag":
        latest_tag = latest_aio_release_tag()
        if latest_tag:
            print(latest_tag)
    elif args.command == "latest-changelog-version":
        print(latest_changelog_version(args.changelog))
    elif args.command == "find-release-commit":
        print(find_release_commit(args.version))
    else:
        print(extract_release_notes(args.version, args.changelog))


if __name__ == "__main__":
    main()
