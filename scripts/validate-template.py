#!/usr/bin/env python3
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "mem0-aio.xml"

REQUIRED_TARGETS = {
    "3000",
    "8765",
    "/mem0/storage",
    "OPENAI_API_KEY",
    "USER",
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_USER_ID",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "OLLAMA_BASE_URL",
    "OLLAMA_HOST",
    "EMBEDDER_PROVIDER",
    "EMBEDDER_MODEL",
    "EMBEDDER_API_KEY",
    "EMBEDDER_BASE_URL",
    "DATABASE_URL",
    "QDRANT_HOST",
    "QDRANT_PORT",
    "CHROMA_HOST",
    "CHROMA_PORT",
    "WEAVIATE_CLUSTER_URL",
    "WEAVIATE_HOST",
    "WEAVIATE_PORT",
    "REDIS_URL",
    "PG_HOST",
    "PG_PORT",
    "PG_DB",
    "PG_USER",
    "PG_PASSWORD",
    "MILVUS_HOST",
    "MILVUS_PORT",
    "MILVUS_TOKEN",
    "MILVUS_DB_NAME",
    "ELASTICSEARCH_HOST",
    "ELASTICSEARCH_PORT",
    "ELASTICSEARCH_USER",
    "ELASTICSEARCH_PASSWORD",
    "OPENSEARCH_HOST",
    "OPENSEARCH_PORT",
    "FAISS_PATH",
    "API_KEY",
    "EXPORT_USER_ID",
    "EXPORT_APP_ID",
    "EXPORT_FROM_DATE",
    "EXPORT_TO_DATE",
    "QDRANT__TELEMETRY_DISABLED",
}

REQUIRED_CHANGELOG_LINK = "https://github.com/JSONbored/mem0-aio/releases"


def main() -> int:
    tree = ET.parse(TEMPLATE_PATH)  # nosec B314
    root = tree.getroot()

    targets = {
        elem.attrib["Target"]
        for elem in root.findall(".//Config")
        if "Target" in elem.attrib and elem.attrib["Target"]
    }

    missing = sorted(REQUIRED_TARGETS - targets)
    if missing:
        print("mem0-aio.xml is missing required runtime targets:", file=sys.stderr)
        for target in missing:
            print(f"  - {target}", file=sys.stderr)
        return 1

    overview = (root.findtext("Overview") or "").strip()
    if not overview:
        print("mem0-aio.xml is missing a non-empty <Overview>", file=sys.stderr)
        return 1

    changes = (root.findtext("Changes") or "").strip()
    if not changes:
        print("mem0-aio.xml is missing a non-empty <Changes> section", file=sys.stderr)
        return 1
    if REQUIRED_CHANGELOG_LINK not in changes:
        print(
            "mem0-aio.xml <Changes> does not include the canonical GitHub releases URL",
            file=sys.stderr,
        )
        return 1

    invalid_option_configs: list[str] = []
    invalid_pipe_configs: list[str] = []
    for config in root.findall(".//Config"):
        name = config.attrib.get("Name", config.attrib.get("Target", "<unnamed>"))
        if config.findall("Option"):
            invalid_option_configs.append(name)

        default = config.attrib.get("Default", "")
        if "|" not in default:
            continue

        allowed_values = default.split("|")
        selected_value = (config.text or "").strip()
        if selected_value not in allowed_values:
            invalid_pipe_configs.append(
                f"{name} (selected={selected_value!r}, allowed={allowed_values!r})"
            )

    if invalid_option_configs:
        print(
            "mem0-aio.xml uses nested <Option> tags, which are not allowed by the catalog-safe template format:",
            file=sys.stderr,
        )
        for name in invalid_option_configs:
            print(f"  - {name}", file=sys.stderr)
        return 1

    if invalid_pipe_configs:
        print(
            "mem0-aio.xml has pipe-delimited defaults whose selected value is not one of the allowed options:",
            file=sys.stderr,
        )
        for detail in invalid_pipe_configs:
            print(f"  - {detail}", file=sys.stderr)
        return 1

    print(
        f"mem0-aio.xml parsed successfully and includes {len(REQUIRED_TARGETS)} required targets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
