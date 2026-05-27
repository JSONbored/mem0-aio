from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path

from defusedxml import ElementTree as ET

from tests.conftest import REPO_ROOT


def _template_configs() -> dict[str, ET.Element]:
    root = ET.parse(REPO_ROOT / "mem0-aio.xml").getroot()
    return {config.attrib["Name"]: config for config in root.findall("Config")}


def _template_root() -> ET.Element:
    return ET.parse(REPO_ROOT / "mem0-aio.xml").getroot()


def test_ca_metadata_uses_current_categories_and_discovery_fields() -> None:
    root = _template_root()

    assert root.findtext("Category") == "AI Productivity Tools:Utilities"  # nosec B101
    assert (
        root.findtext("ReadMe") == "https://github.com/JSONbored/mem0-aio#readme"
    )  # nosec B101
    assert [s.text for s in root.findall("Screenshot")] == [  # nosec B101
        "https://raw.githubusercontent.com/JSONbored/awesome-unraid/main/screenshots/mem0-aio/01-home.png",
        "https://raw.githubusercontent.com/JSONbored/awesome-unraid/main/screenshots/mem0-aio/02-memories.png",
        "https://raw.githubusercontent.com/JSONbored/awesome-unraid/main/screenshots/mem0-aio/03-settings.png",
    ]


def test_api_mcp_port_is_not_published_by_default() -> None:
    root = ET.parse(REPO_ROOT / "mem0-aio.xml").getroot()
    published_ports = {
        (
            port.findtext("HostPort", default=""),
            port.findtext("ContainerPort", default=""),
        )
        for port in root.findall("./Networking/Publish/Port")
    }
    configs = _template_configs()

    assert ("3000", "3000") in published_ports  # nosec B101
    assert ("8765", "8765") not in published_ports  # nosec B101

    api_port = configs["API / MCP Port"]
    assert api_port.attrib["Display"] == "advanced"  # nosec B101
    assert api_port.attrib["Required"] == "false"  # nosec B101
    assert api_port.attrib["Default"] == ""  # nosec B101
    assert (api_port.text or "") == ""  # nosec B101

    api_bind = configs["[Security] API Bind Address (MEM0_API_HOST)"]
    assert api_bind.attrib["Target"] == "MEM0_API_HOST"  # nosec B101
    assert api_bind.attrib["Default"] == "127.0.0.1"  # nosec B101
    assert api_bind.text == "127.0.0.1"  # nosec B101


def test_fastapi_binds_to_container_localhost_by_default() -> None:
    run_script = (REPO_ROOT / "rootfs/etc/services.d/fastapi/run").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert '--host "${MEM0_API_HOST:-127.0.0.1}"' in run_script  # nosec B101
    assert "ENV MEM0_API_HOST=127.0.0.1" in dockerfile  # nosec B101
    assert "EXPOSE 3000 6333" in dockerfile  # nosec B101
    assert "EXPOSE 3000 8765 6333" not in dockerfile  # nosec B101


def test_provider_auto_sentinel_is_unset_before_runtime_env_persistence() -> None:
    bootstrap = (REPO_ROOT / "rootfs/etc/cont-init.d/01-bootstrap.sh").read_text()

    assert (  # nosec B101
        "for provider_var in LLM_PROVIDER EMBEDDER_PROVIDER" in bootstrap
    )
    assert '[[ ${!provider_var-} == "auto" ]]' in bootstrap  # nosec B101
    assert 'unset "${provider_var}"' in bootstrap  # nosec B101
    assert "[[ -n ${OLLAMA_BASE_URL-} ]]" in bootstrap  # nosec B101
    assert 'export LLM_PROVIDER="${LLM_PROVIDER:-ollama}"' in bootstrap  # nosec B101
    assert (  # nosec B101
        'export EMBEDDER_PROVIDER="${EMBEDDER_PROVIDER:-ollama}"' in bootstrap
    )


def test_openai_categorization_is_optional_for_local_provider_boot() -> None:
    patcher = (REPO_ROOT / "docker/patch-openmemory.py").read_text()
    package_patcher = (REPO_ROOT / "docker/patch-mem0-package.py").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert "get_default_memory_config" in patcher  # nosec B101
    assert "wrapper environment defaults" in patcher  # nosec B101
    assert "redisvl" in patcher  # nosec B101
    assert "chromadb" in patcher  # nosec B101
    assert "faiss-cpu" in patcher  # nosec B101
    assert "elasticsearch>=8,<9" in patcher  # nosec B101
    assert "qdrant_is_external" in patcher  # nosec B101
    assert "Keep this precedence aligned" in patcher  # nosec B101
    assert "def _get_embedding_model_dims()" in patcher  # nosec B101
    assert 'os.environ.get("EMBEDDER_DIMENSIONS")' in patcher  # nosec B101
    assert '"nomic-embed-text": 768' in patcher  # nosec B101
    assert 'vector_store_config["embedding_model_dims"]' in patcher  # nosec B101
    assert "elasticsearch_scheme" in patcher  # nosec B101
    assert "ELASTICSEARCH_USE_SSL" in patcher  # nosec B101
    assert "ELASTICSEARCH_PASSWORD is required" in patcher  # nosec B101
    assert "ELASTICSEARCH_PASSWORD', 'changeme'" not in patcher  # nosec B101
    assert "with config: {vector_store_config}" not in patcher  # nosec B101
    assert 'Path("/app/api/app/mcp_server.py")' in patcher  # nosec B101
    assert "top_k=10" in patcher  # nosec B101
    assert "openai_client = None" in patcher  # nosec B101
    assert "def _get_openai_client()" in patcher  # nosec B101
    assert 'os.environ.get("OPENAI_API_KEY")' in patcher  # nosec B101
    assert 'os.environ.get("OPENAI_ADMIN_KEY")' in patcher  # nosec B101
    assert "return []" in patcher  # nosec B101
    assert "OpenAI()" in patcher  # nosec B101
    assert "COPY docker/patch-mem0-package.py" in dockerfile  # nosec B101
    assert "bulk(self.client, actions, refresh=True)" in package_patcher  # nosec B101


def test_external_search_backends_verify_tls_by_default() -> None:
    configs = _template_configs()

    assert (  # nosec B101
        configs["[Vector Store:Elasticsearch] Verify Certs"].text == "true"
    )
    assert (  # nosec B101
        configs["[Vector Store:OpenSearch] Verify Certs"].text == "true"
    )


def test_dockerfile_normalizes_apt_sources_before_update() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    normalizer = (REPO_ROOT / "docker/normalize-apt-sources.sh").read_text()

    ca_index = dockerfile.index("COPY --from=qdrant-bin /etc/ssl/certs /etc/ssl/certs")
    source_guard_index = dockerfile.index("/usr/local/bin/normalize-apt-sources")
    update_index = dockerfile.index("apt-get update")
    install_index = dockerfile.index("apt-get install -y --no-install-recommends")

    assert "FROM ubuntu:26.04@" in dockerfile  # nosec B101
    assert " AS runtime-base" in dockerfile  # nosec B101
    assert "FROM runtime-base AS runtime" in dockerfile  # nosec B101
    assert "COPY docker/normalize-apt-sources.sh" in dockerfile  # nosec B101
    assert ca_index < source_guard_index  # nosec B101
    assert source_guard_index < update_index  # nosec B101
    assert update_index < install_index  # nosec B101
    assert (  # nosec B101
        'Acquire::https::CaInfo "/etc/ssl/certs/ca-certificates.crt"' in dockerfile
    )
    assert 'Acquire::Retries "3"' in dockerfile  # nosec B101
    assert 'Acquire::Queue-Mode "host"' in dockerfile  # nosec B101
    assert 'Acquire::ForceIPv4 "true"' in dockerfile  # nosec B101
    assert 'Acquire::http::Pipeline-Depth "0"' in dockerfile  # nosec B101
    assert 'Acquire::https::Pipeline-Depth "0"' in dockerfile  # nosec B101
    assert 'Acquire::http::Timeout "20"' in dockerfile  # nosec B101
    assert 'Acquire::https::Timeout "20"' in dockerfile  # nosec B101
    assert 'Acquire::https::Verify-Peer "true"' in dockerfile  # nosec B101
    assert 'Acquire::https::Verify-Host "true"' in dockerfile  # nosec B101
    assert 'Acquire::Check-Valid-Until "true"' in dockerfile  # nosec B101
    assert 'Acquire::AllowInsecureRepositories "false"' in dockerfile  # nosec B101
    assert (  # nosec B101
        'Acquire::AllowDowngradeToInsecureRepositories "false"' in dockerfile
    )
    assert 'APT::Update::Error-Mode "any"' in dockerfile  # nosec B101
    assert "ubuntu-archive-keyring.gpg" in dockerfile  # nosec B101
    assert "http://archive.ubuntu.com/ubuntu/|" not in dockerfile  # nosec B101
    assert "http://security.ubuntu.com/ubuntu/|" not in dockerfile  # nosec B101
    assert "http://ports.ubuntu.com/ubuntu-ports/|" not in dockerfile  # nosec B101
    assert "sed -i 's|http://|https://|g'" not in dockerfile  # nosec B101
    assert "apt_update_ok=0" in dockerfile  # nosec B101
    assert 'test "${apt_update_ok}" = "1"' in dockerfile  # nosec B101
    assert "unable to resolve apt package version" in dockerfile  # nosec B101
    assert "insecure apt source option is not allowed" in normalizer  # nosec B101
    assert "plaintext apt source remained" in normalizer  # nosec B101
    assert "http://archive\\.ubuntu\\.com/ubuntu/" in normalizer  # nosec B101
    assert "http://security\\.ubuntu\\.com/ubuntu/" in normalizer  # nosec B101
    assert "http://ports\\.ubuntu\\.com/ubuntu-ports/" in normalizer  # nosec B101
    assert "https://archive.ubuntu.com/ubuntu/" in normalizer  # nosec B101
    assert "https://security.ubuntu.com/ubuntu/" in normalizer  # nosec B101
    assert "https://ports.ubuntu.com/ubuntu-ports/" in normalizer  # nosec B101


def _apt_source_root(tmp_path: Path) -> Path:
    root = tmp_path / "apt-root"
    (root / "etc/apt/sources.list.d").mkdir(parents=True)
    return root


def _run_apt_normalizer(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        [str(REPO_ROOT / "docker/normalize-apt-sources.sh"), str(root)],
        check=False,
        text=True,
        capture_output=True,
    )


def test_apt_normalizer_rewrites_official_sources_files(tmp_path: Path) -> None:
    root = _apt_source_root(tmp_path)
    deb822 = root / "etc/apt/sources.list.d/ubuntu.sources"
    legacy = root / "etc/apt/sources.list.d/ports.list"
    deb822.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: http://archive.ubuntu.com/ubuntu/ http://security.ubuntu.com/ubuntu/",
                "Suites: resolute resolute-updates resolute-security",
                "Components: main universe",
                "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg",
            ]
        )
        + "\n"
    )
    legacy.write_text("deb http://ports.ubuntu.com/ubuntu-ports/ resolute main\n")

    result = _run_apt_normalizer(root)

    assert result.returncode == 0, result.stderr  # nosec B101
    assert "http://" not in deb822.read_text()  # nosec B101
    assert "http://" not in legacy.read_text()  # nosec B101
    assert "https://archive.ubuntu.com/ubuntu/" in deb822.read_text()  # nosec B101
    assert "https://security.ubuntu.com/ubuntu/" in deb822.read_text()  # nosec B101
    assert "https://ports.ubuntu.com/ubuntu-ports/" in legacy.read_text()  # nosec B101


def test_apt_normalizer_rejects_remaining_plaintext_sources(tmp_path: Path) -> None:
    root = _apt_source_root(tmp_path)
    source = root / "etc/apt/sources.list.d/attacker.list"
    source.write_text("deb http://attacker.invalid/ubuntu/ resolute main\n")

    result = _run_apt_normalizer(root)

    assert result.returncode != 0  # nosec B101
    assert "plaintext apt source remained" in result.stderr  # nosec B101


def test_apt_normalizer_rejects_insecure_source_options(tmp_path: Path) -> None:
    root = _apt_source_root(tmp_path)
    source = root / "etc/apt/sources.list.d/ubuntu.sources"
    source.write_text(
        "\n".join(
            [
                "Types: deb",
                "URIs: http://archive.ubuntu.com/ubuntu/",
                "Suites: resolute",
                "Components: main",
                "Trusted: yes",
                "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg",
            ]
        )
        + "\n"
    )

    result = _run_apt_normalizer(root)

    assert result.returncode != 0  # nosec B101
    assert "insecure apt source option is not allowed" in result.stderr  # nosec B101


def test_backend_matrix_bypasses_host_proxy_for_internal_services() -> None:
    from tests.integration.test_backend_matrix import mem0_env_args

    backend_matrix = (
        REPO_ROOT / "tests/integration/test_backend_matrix.py"
    ).read_text()
    env_args = mem0_env_args("redis", "mem0-backend-redis-test")
    expected = "127.0.0.1,localhost,mem0-aio-ollama-mock,mem0-backend-redis-test"

    assert f"NO_PROXY={expected}" in env_args  # nosec B101
    assert f"no_proxy={expected}" in env_args  # nosec B101
    assert "HTTP_PROXY=" in env_args  # nosec B101
    assert "HTTPS_PROXY=" in env_args  # nosec B101
    assert "ALL_PROXY=" in env_args  # nosec B101
    assert '"NO_PROXY=*"' in backend_matrix  # nosec B101
    assert '"no_proxy=*"' in backend_matrix  # nosec B101
    assert "PROXY_ENV_VARS" in backend_matrix  # nosec B101
    assert 'f"{name}="' in backend_matrix  # nosec B101


def test_openmemory_submodule_uses_official_upstream() -> None:
    gitmodules = (REPO_ROOT / ".gitmodules").read_text()
    app_manifest = (REPO_ROOT / ".aio-fleet.yml").read_text()

    assert "url = https://github.com/mem0ai/mem0" in gitmodules  # nosec B101
    assert "url = https://github.com/JSONbored/mem0" not in gitmodules  # nosec B101
    assert "submodule_ref_template" not in app_manifest  # nosec B101
