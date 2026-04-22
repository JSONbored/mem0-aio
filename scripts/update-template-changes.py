#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CHANGELOG = ROOT / "CHANGELOG.md"
GENERATED_NOTE = (
    "- Generated from CHANGELOG.md during release preparation. Do not edit manually."
)


def resolve_template_path() -> pathlib.Path:
    repo_xml = ROOT / f"{ROOT.name}.xml"
    if repo_xml.exists():
        return repo_xml

    xml_files = sorted(ROOT.glob("*.xml"))
    if len(xml_files) == 1:
        return xml_files[0]

    return ROOT / "template-aio.xml"


def extract_release_notes(version: str, changelog: pathlib.Path) -> str:
    heading = re.compile(
        rf"^##\s+(?:\[{re.escape(version)}\]\([^)]+\)|{re.escape(version)})(?:\s+-\s+.+)?$"
    )
    next_heading = re.compile(r"^##\s+")

    lines = changelog.read_text().splitlines()
    start = None
    for idx, line in enumerate(lines):
        if heading.match(line.strip()):
            start = idx + 1
            break

    if start is None:
        raise SystemExit(f"Unable to find release section for {version} in {changelog}")

    end = len(lines)
    for idx in range(start, len(lines)):
        if next_heading.match(lines[idx].strip()):
            end = idx
            break

    notes = "\n".join(lines[start:end]).strip()
    if not notes:
        raise SystemExit(f"Release section for {version} in {changelog} is empty")
    return notes


def release_heading(version: str, changelog: pathlib.Path) -> str:
    heading = re.compile(
        rf"^##\s+(?:\[{re.escape(version)}\]\([^)]+\)|{re.escape(version)})(?:\s+-\s+(.+))?$"
    )
    for line in changelog.read_text().splitlines():
        match = heading.match(line.strip())
        if match:
            release_date = (match.group(1) or "").strip()
            if release_date:
                return f"### {release_date}"
            break
    return f"### {version}"


def build_changes_body(
    version: str,
    notes: str,
    changelog: pathlib.Path,
) -> str:
    lines: list[str] = [release_heading(version, changelog), GENERATED_NOTE]
    for line in notes.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue
        if re.match(r"^\[[^\]]+\]:\s+https?://", stripped):
            continue
        if stripped.startswith("Full Changelog:"):
            continue
        if stripped.startswith("## "):
            continue
        if stripped.startswith("### "):
            continue
        if stripped.startswith(("- ", "* ")):
            lines.append(f"- {stripped[2:].strip()}")
            continue
        lines.append(f"- {stripped}")

    if len(lines) == 2:
        raise SystemExit("Release notes did not produce any bullet lines for <Changes>")

    return "\n".join(lines).strip()


def encode_for_template(body: str) -> str:
    escaped = html.escape(body, quote=False)
    return escaped.replace("\n", "&#xD;\n")


def update_template(template_path: pathlib.Path, encoded_changes: str) -> None:
    content = template_path.read_text()
    pattern = re.compile(r"<Changes>.*?</Changes>", re.DOTALL)
    replacement = f"<Changes>{encoded_changes}</Changes>"
    updated, count = pattern.subn(replacement, content, count=1)
    if count != 1:
        raise SystemExit(f"Expected exactly one <Changes> block in {template_path}")
    template_path.write_text(updated)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update the template XML <Changes> block from CHANGELOG release notes."
    )
    parser.add_argument("version", help="Release version (example: v0.2.0)")
    parser.add_argument("--changelog", type=pathlib.Path, default=DEFAULT_CHANGELOG)
    parser.add_argument("--template", type=pathlib.Path, default=None)
    args = parser.parse_args()

    template_path = args.template or resolve_template_path()
    notes = extract_release_notes(args.version, args.changelog)
    body = build_changes_body(args.version, notes, args.changelog)
    update_template(template_path, encode_for_template(body))
    print(
        f"Updated <Changes> in {template_path} from {args.changelog} for {args.version}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
