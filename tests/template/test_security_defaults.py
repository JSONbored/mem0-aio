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

    api_bind = configs["[Security] API Bind Address"]
    assert api_bind.attrib["Target"] == "MEM0_API_HOST"  # nosec B101
    assert api_bind.attrib["Default"] == "127.0.0.1"  # nosec B101
    assert api_bind.text == "127.0.0.1"  # nosec B101


def test_fastapi_binds_to_container_localhost_by_default() -> None:
    run_script = (REPO_ROOT / "rootfs/etc/services.d/fastapi/run").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert '--host "${MEM0_API_HOST:-127.0.0.1}"' in run_script  # nosec B101
    assert "--host 0.0.0.0" not in run_script  # nosec B101
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


def test_dockerfile_rewrites_apt_sources_to_https_before_update() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    ca_index = dockerfile.index("COPY --from=qdrant-bin /etc/ssl/certs /etc/ssl/certs")
    rewrite_index = dockerfile.index("sed -i 's|http://|https://|g'")
    update_index = dockerfile.index("apt-get update")
    install_index = dockerfile.index("apt-get install -y --no-install-recommends")

    assert ca_index < rewrite_index  # nosec B101
    assert rewrite_index < update_index  # nosec B101
    assert update_index < install_index  # nosec B101
    assert (  # nosec B101
        'Acquire::https::CaInfo "/etc/ssl/certs/ca-certificates.crt"' in dockerfile
    )
    assert 'APT::Update::Error-Mode "any"' in dockerfile  # nosec B101
    assert 'Acquire::Queue-Mode "access"' in dockerfile  # nosec B101
    assert "apt_update_ok=0" in dockerfile  # nosec B101
    assert 'test "${apt_update_ok}" = "1"' in dockerfile  # nosec B101
    assert "unable to resolve apt package version" in dockerfile  # nosec B101


def test_openmemory_submodule_uses_official_upstream() -> None:
    gitmodules = (REPO_ROOT / ".gitmodules").read_text()
    app_manifest = (REPO_ROOT / ".aio-fleet.yml").read_text()

    assert "url = https://github.com/mem0ai/mem0" in gitmodules  # nosec B101
    assert "url = https://github.com/JSONbored/mem0" not in gitmodules  # nosec B101
    assert "submodule_ref_template" not in app_manifest  # nosec B101
