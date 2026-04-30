from __future__ import annotations

from pathlib import Path

BUILD_WORKFLOW = Path(".github/workflows/build.yml")
PYTEST_ACTION = Path(".github/actions/run-pytest/action.yml")
REUSABLE_REF = "8e06c828cec34bbdcc6c339f01d95d738f525be8"
EXPECTED_INPUT_LINES = [
    "app_slug: mem0-aio",
    "image_name: jsonbored/mem0-aio",
    "workflow_title: CI / Mem0 AIO",
    "docker_cache_scope: mem0-aio-image",
    "pytest_image_tag: mem0-aio:pytest",
    "publish_profile: changelog-version",
    "upstream_name: Mem0",
    "image_description: Unraid-first AIO wrapper image for Mem0 and OpenMemory",
    'python_version: "3.13"',
    "trunk_org_slug: aethereal",
    "publish_platforms: linux/amd64,linux/arm64",
    "checkout_submodules: true",
    "integration_pytest_args: tests/integration -m integration",
    "run_extended_integration: false",
    'extended_integration_pytest_args: ""',
    'generator_check_command: ""',
    "upstream_digest_arg: UPSTREAM_IMAGE_DIGEST",
]
EXPECTED_AGENT_INPUT_LINES = []
EXPECTED_WATCHED_PATHS = [
    ".github/actions/**",
    ".github/workflows/**",
    ".trunk/**",
    "CHANGELOG.md",
    "Dockerfile",
    "assets/**",
    "cliff.toml",
    "components.toml",
    "components/**",
    "docs/upstream/**",
    "mem0-aio.xml",
    "openmemory",
    "openmemory/**",
    "pyproject.toml",
    "renovate.json",
    "requirements-dev.txt",
    "rootfs/**",
    "scripts/**",
    "tests/**",
    "upstream.toml",
]
EXPECTED_XML_PATHS = ["mem0-aio.xml", "assets/**"]
EXPECTED_EXTRA_PUBLISH_PATHS = ["openmemory", "openmemory/**"]
EXPECTED_CATALOG_ASSETS = [
    "mem0-aio.xml|mem0-aio.xml",
    "assets/app-icon.png|icons/mem0.png",
]
ALLOWED_CREATE_PULL_REQUEST_REF = (
    "peter-evans/create-pull-request@"
    "5f6978faf089d4d20b00c7766989d076bb2fc7f1 # v8.1.1"
)


def _workflow() -> str:
    return BUILD_WORKFLOW.read_text()


def test_build_workflow_uses_pinned_aio_fleet_reusable_workflow() -> None:
    workflow = _workflow()

    assert (  # nosec B101
        "uses: JSONbored/aio-fleet/.github/workflows/aio-build.yml@" f"{REUSABLE_REF}"
    ) in workflow
    assert "@main" not in workflow  # nosec B101
    assert "secrets: inherit" in workflow  # nosec B101
    assert "packages: write" in workflow  # nosec B101
    assert "pull-requests: write" in workflow  # nosec B101
    assert "docker/build-push-action" not in workflow  # nosec B101
    assert "detect-changes:" not in workflow  # nosec B101


def test_build_workflow_passes_expected_repo_inputs() -> None:
    workflow = _workflow()

    for line in EXPECTED_INPUT_LINES:
        assert f"      {line}" in workflow  # nosec B101
    for line in EXPECTED_AGENT_INPUT_LINES:
        assert f"      {line}" in workflow  # nosec B101


def test_build_workflow_watches_expected_paths() -> None:
    workflow = _workflow()

    for path in EXPECTED_WATCHED_PATHS:
        assert f'      - "{path}"' in workflow  # nosec B101


def test_build_workflow_passes_template_and_catalog_assets() -> None:
    workflow = _workflow()

    for path in EXPECTED_XML_PATHS:
        assert path in workflow  # nosec B101
    for path in EXPECTED_EXTRA_PUBLISH_PATHS:
        assert path in workflow  # nosec B101
    for asset in EXPECTED_CATALOG_ASSETS:
        assert asset in workflow  # nosec B101


def test_local_pytest_action_remains_available_to_reusable_workflow() -> None:
    assert PYTEST_ACTION.exists()  # nosec B101
    assert "trunk-io/analytics-uploader@" in PYTEST_ACTION.read_text()  # nosec B101


def test_release_workflows_use_org_allowed_create_pull_request_pin() -> None:
    workflow_paths = list(Path(".github/workflows").glob("release*.yml"))
    for workflow_path in workflow_paths:
        workflow = workflow_path.read_text()
        if "peter-evans/create-pull-request@" not in workflow:
            continue
        assert ALLOWED_CREATE_PULL_REQUEST_REF in workflow  # nosec B101
        assert "peter-evans/create-pull-request@c0f553" not in workflow  # nosec B101
