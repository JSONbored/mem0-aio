from __future__ import annotations

from defusedxml import ElementTree as ET

from tests.conftest import REPO_ROOT


def _template_configs() -> dict[str, ET.Element]:
    root = ET.parse(REPO_ROOT / "mem0-aio.xml").getroot()
    return {config.attrib["Name"]: config for config in root.findall("Config")}


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


def test_external_search_backends_verify_tls_by_default() -> None:
    configs = _template_configs()

    assert (  # nosec B101
        configs["[Vector Store:Elasticsearch] Verify Certs"].text == "true"
    )
    assert (  # nosec B101
        configs["[Vector Store:OpenSearch] Verify Certs"].text == "true"
    )


def test_dockerfile_restricts_apt_sources_without_forcing_https() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    ca_index = dockerfile.index("COPY --from=qdrant-bin /etc/ssl/certs /etc/ssl/certs")
    source_guard_index = dockerfile.index("unsupported apt source")
    update_index = dockerfile.index("apt-get update")
    install_index = dockerfile.index("apt-get install -y --no-install-recommends")

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
    assert "insecure apt source option is not allowed" in dockerfile  # nosec B101
    assert "http://archive.ubuntu.com/ubuntu/" in dockerfile  # nosec B101
    assert "http://security.ubuntu.com/ubuntu/" in dockerfile  # nosec B101
    assert "http://ports.ubuntu.com/ubuntu-ports/" in dockerfile  # nosec B101
    assert "https://archive.ubuntu.com/ubuntu/" in dockerfile  # nosec B101
    assert "https://security.ubuntu.com/ubuntu/" in dockerfile  # nosec B101
    assert "https://ports.ubuntu.com/ubuntu-ports/" in dockerfile  # nosec B101
    assert "https://*|" not in dockerfile  # nosec B101
    assert "sed -i 's|http://|https://|g'" not in dockerfile  # nosec B101
    assert "apt_update_ok=0" in dockerfile  # nosec B101
    assert 'test "${apt_update_ok}" = "1"' in dockerfile  # nosec B101
    assert "unable to resolve apt package version" in dockerfile  # nosec B101


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


def test_openmemory_submodule_uses_aio_patch_fork() -> None:
    gitmodules = (REPO_ROOT / ".gitmodules").read_text()
    app_manifest = (REPO_ROOT / ".aio-fleet.yml").read_text()

    assert "url = https://github.com/JSONbored/mem0" in gitmodules  # nosec B101
    assert (  # nosec B101
        "submodule_ref_template: codex/openmemory-{version}-aio" in app_manifest
    )
