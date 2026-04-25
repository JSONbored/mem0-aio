from __future__ import annotations

import json
import re
from pathlib import Path

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"

SECRET_KEYWORDS = (
    "ACCESS_KEY",
    "API_KEY",
    "AUTH_TOKEN",
    "CLIENT_SECRET",
    "PASSWORD",
    "PRIVATE_KEY",
    "SECRET",
    "TOKEN",
)


def _template_path() -> Path:
    candidates = sorted(ROOT.glob("*.xml"))
    assert candidates, "repository must include an Unraid XML template"  # nosec B101
    return candidates[0]


def _template_root() -> ET.Element:
    return ET.parse(_template_path()).getroot()


def _dockerfile_text() -> str:
    return DOCKERFILE.read_text()


def _dockerfile_volumes() -> set[str]:
    volumes: set[str] = set()
    for match in re.finditer(r"(?m)^VOLUME\s+(\[[^\]]+\])", _dockerfile_text()):
        volumes.update(json.loads(match.group(1)))
    return volumes


def _exposed_ports() -> set[str]:
    ports: set[str] = set()
    for line in _dockerfile_text().splitlines():
        if not line.startswith("EXPOSE "):
            continue
        for token in line.split()[1:]:
            ports.add(token.split("/", 1)[0])
    return ports


def _arg_defaults() -> dict[str, str]:
    defaults: dict[str, str] = {}
    for line in _dockerfile_text().splitlines():
        if not line.startswith("ARG ") or "=" not in line:
            continue
        name, value = line.removeprefix("ARG ").split("=", 1)
        defaults[name] = value
    return defaults


def _config_elements() -> list[ET.Element]:
    return list(_template_root().findall("Config"))


def test_unraid_metadata_contract_is_complete_and_unprivileged() -> None:
    root = _template_root()

    assert root.findtext("Privileged") == "false"  # nosec B101
    for tag in (
        "Name",
        "Repository",
        "Support",
        "Project",
        "TemplateURL",
        "Icon",
        "Category",
        "WebUI",
    ):
        value = root.findtext(tag)
        assert value and value.strip(), f"{tag} must be populated"  # nosec B101
    assert (
        _config_elements()
    ), "template must expose configurable settings"  # nosec B101


def test_secret_like_template_variables_are_masked() -> None:
    for config in _config_elements():
        name = config.get("Name") or ""
        target = config.get("Target") or ""
        default = config.get("Default") or ""
        if (
            target.endswith("_PATH")
            or target.endswith("_ENABLED")
            or target.startswith(("MAX_", "MIN_"))
            or name.upper().endswith(" PATH")
            or set(default.split("|")) == {"false", "true"}
        ):
            continue
        haystack = " ".join(filter(None, (name, target))).upper()
        if any(keyword in haystack for keyword in SECRET_KEYWORDS):
            assert (
                config.get("Mask") == "true"
            ), (  # nosec B101
                f"{config.get('Name') or config.get('Target')} should be masked"
            )


def test_required_appdata_paths_are_declared_as_container_volumes() -> None:
    volumes = _dockerfile_volumes()
    assert volumes, "Dockerfile must declare persistent volumes"  # nosec B101

    for config in _config_elements():
        if config.get("Type") != "Path" or config.get("Required") != "true":
            continue
        default = config.get("Default") or config.text or ""
        target = config.get("Target") or ""
        if not default.startswith("/mnt/user/appdata"):
            continue
        assert any(
            target == volume or target.startswith(f"{volume.rstrip('/')}/")
            for volume in volumes
        ), f"{target} must be covered by a Dockerfile VOLUME"  # nosec B101


def test_template_ports_are_exposed_by_image() -> None:
    exposed_ports = _exposed_ports()
    assert exposed_ports, "Dockerfile must expose template ports"  # nosec B101

    for config in _config_elements():
        if config.get("Type") == "Port":
            assert config.get("Target") in exposed_ports  # nosec B101


def test_dockerfile_has_runtime_safety_contract() -> None:
    dockerfile = _dockerfile_text()
    arg_defaults = _arg_defaults()
    from_lines = [
        line.split()[1] for line in dockerfile.splitlines() if line.startswith("FROM ")
    ]

    assert from_lines, "Dockerfile must declare at least one base image"  # nosec B101
    for image in from_lines:
        digest_arg = re.search(r"@\$\{([^}]+)\}", image)
        assert "@sha256:" in image or (  # nosec B101
            digest_arg
            and arg_defaults.get(digest_arg.group(1), "").startswith("sha256:")
        ), f"{image} must be digest-pinned"

    assert "HEALTHCHECK" in dockerfile  # nosec B101
    assert "curl -fsS" in dockerfile  # nosec B101
    assert 'ENTRYPOINT ["/init"]' in dockerfile  # nosec B101
    assert "S6_CMD_WAIT_FOR_SERVICES_MAXTIME" in dockerfile  # nosec B101
    assert "S6_BEHAVIOUR_IF_STAGE2_FAILS=2" in dockerfile  # nosec B101


def test_docker_socket_mount_is_advanced_and_documented_when_present() -> None:
    for config in _config_elements():
        if config.get("Target") != "/var/run/docker.sock":
            continue
        description = (config.get("Description") or "").lower()
        assert config.get("Display") == "advanced"  # nosec B101
        assert config.get("Required") == "false"  # nosec B101
        assert "socket" in description and "security" in description  # nosec B101
