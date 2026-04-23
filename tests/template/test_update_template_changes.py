from __future__ import annotations

import sys
from pathlib import Path

from tests.helpers import run_command


def test_update_template_changes_uses_date_first_bullets(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "\n".join(
            [
                "# Changelog",
                "",
                "## v1.2.3 - 2026-04-21",
                "",
                "- First shipped change",
                "* Second shipped change",
                "Plain sentence without a list marker",
                "",
            ]
        )
    )

    template = tmp_path / "template-aio.xml"
    template.write_text(
        "\n".join(
            [
                '<?xml version="1.0"?>',
                '<Container version="2">',
                "  <Changes>placeholder</Changes>",
                "</Container>",
            ]
        )
    )

    run_command(
        [
            sys.executable,
            "scripts/update-template-changes.py",
            "v1.2.3",
            "--changelog",
            str(changelog),
            "--template",
            str(template),
        ]
    )

    changes = template.read_text()
    assert "### 2026-04-21" in changes  # nosec B101
    assert "- First shipped change" in changes  # nosec B101
    assert "- Second shipped change" in changes  # nosec B101
    assert "- Plain sentence without a list marker" in changes  # nosec B101
    assert "GitHub Releases" not in changes  # nosec B101
