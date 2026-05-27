from pathlib import Path


def replace_required(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"OpenMemory patch anchor not found: {label}")
    return text.replace(old, new, 1)


def replace_between_required(
    text: str, start_marker: str, end_marker: str, replacement: str, label: str
) -> str:
    start = text.find(start_marker)
    if start == -1:
        raise RuntimeError(f"OpenMemory patch anchor not found: {label} start")
    end = text.find(end_marker, start)
    if end == -1:
        raise RuntimeError(f"OpenMemory patch anchor not found: {label} end")
    return text[:start] + replacement + text[end + len(end_marker) :]


def require_contains(text: str, marker: str, label: str) -> None:
    if marker not in text:
        raise RuntimeError(f"OpenMemory patch verification failed: {label}")


database = Path("/app/api/app/database.py")
database.write_text(
    replace_required(
        database.read_text(),
        """# SQLAlchemy engine & session\nengine = create_engine(\n    DATABASE_URL,\n    connect_args={\"check_same_thread\": False}  # Needed for SQLite\n)\n""",
        """engine_kwargs = {}\nif DATABASE_URL.startswith(\"sqlite\"):\n    engine_kwargs[\"connect_args\"] = {\"check_same_thread\": False}\n\n# SQLAlchemy engine & session\nengine = create_engine(\n    DATABASE_URL,\n    **engine_kwargs,\n)\n""",
        "database engine kwargs",
    )
)

schemas = Path("/app/api/app/schemas.py")
schemas_text = replace_required(
    schemas.read_text(),
    "from pydantic import BaseModel, ConfigDict, Field, validator",
    "from pydantic import BaseModel, ConfigDict, Field, field_validator",
    "pydantic validator import",
)
schemas_text = replace_required(
    schemas_text,
    "    @validator('created_at', pre=True)\n    def convert_to_epoch(cls, v):",
    "    @field_validator('created_at', mode='before')\n    @classmethod\n    def convert_to_epoch(cls, v):",
    "created_at validator",
)
schemas.write_text(schemas_text)

requirements = Path("/app/api/requirements.txt")
requirements_text = requirements.read_text()
for requirement in (
    "redis",
    "redisvl",
    "chromadb",
    "weaviate-client",
    "elasticsearch>=8,<9",
    "opensearch-py",
    "faiss-cpu",
):
    if requirement not in requirements_text:
        requirements_text += f"\n{requirement}"
requirements.write_text(requirements_text + "\n")

config = Path("/app/api/app/routers/config.py")
config_text = replace_required(
    config.read_text(),
    "from app.utils.memory import reset_memory_client",
    "from app.utils.memory import get_default_memory_config, reset_memory_client",
    "config imports memory defaults",
)
config_text = replace_required(
    config_text,
    '''def get_default_configuration():
    """Get the default configuration with sensible defaults for LLM and embedder."""
    return {
        "openmemory": {
            "custom_instructions": None
        },
        "mem0": {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "api_key": "env:OPENAI_API_KEY"
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": "env:OPENAI_API_KEY"
                }
            },
            "vector_store": None
        }
    }
''',
    '''def get_default_configuration():
    """Get the default configuration with wrapper environment defaults."""
    mem0_config = get_default_memory_config()
    return {
        "openmemory": {
            "custom_instructions": None
        },
        "mem0": {
            "llm": mem0_config["llm"],
            "embedder": mem0_config["embedder"],
            "vector_store": mem0_config.get("vector_store")
        }
    }
''',
    "default OpenMemory configuration",
)
config.write_text(config_text)

memory = Path("/app/api/app/utils/memory.py")
memory_text = memory.read_text().replace("    \n", "\n").replace("        \n", "\n")
memory_text = replace_required(
    memory_text,
    """_EMBEDDER_CONFIG_FACTORIES = {
    "ollama": _build_ollama_embedder_config,
    "openai": _build_openai_embedder_config,
}
""",
    """_EMBEDDER_CONFIG_FACTORIES = {
    "ollama": _build_ollama_embedder_config,
    "openai": _build_openai_embedder_config,
}


def _get_embedding_model_dims():
    explicit_dims = os.environ.get("EMBEDDER_DIMENSIONS")
    if explicit_dims:
        return int(explicit_dims)

    provider = (
        os.environ.get("EMBEDDER_PROVIDER")
        or os.environ.get("LLM_PROVIDER")
        or ""
    ).lower()
    if provider != "ollama" and not os.environ.get("OLLAMA_BASE_URL"):
        return None

    model = (os.environ.get("EMBEDDER_MODEL") or "nomic-embed-text").split(":", 1)[0].lower()
    known_ollama_dims = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
    }
    return known_ollama_dims.get(model)
""",
    "embedding dimensions helper",
)

vector_start = '    vector_store_config = {\n        "collection_name": "openmemory",\n        "host": "mem0_store",\n    }\n'
vector_end = "\n\n    # Detect LLM provider from environment variables\n"
vector_block = """    qdrant_host = os.environ.get("QDRANT_HOST", "127.0.0.1")
    qdrant_port = os.environ.get("QDRANT_PORT", "6333")
    qdrant_is_external = bool(
        os.environ.get("QDRANT_URL")
        or os.environ.get("QDRANT_API_KEY")
        or qdrant_host not in {"127.0.0.1", "localhost", ""}
    )

    vector_store_config = {
        "collection_name": "openmemory",
        "host": "mem0_store",
    }

    # Keep this precedence aligned with mem0-aio's shell validation helper.
    if os.environ.get('CHROMA_HOST') and os.environ.get('CHROMA_PORT'):
        vector_store_provider = "chroma"
        vector_store_config.update({
            "host": os.environ.get('CHROMA_HOST'),
            "port": int(os.environ.get('CHROMA_PORT'))
        })
    elif os.environ.get('WEAVIATE_CLUSTER_URL') or (os.environ.get('WEAVIATE_HOST') and os.environ.get('WEAVIATE_PORT')):
        vector_store_provider = "weaviate"
        cluster_url = os.environ.get('WEAVIATE_CLUSTER_URL')
        if not cluster_url:
            weaviate_host = os.environ.get('WEAVIATE_HOST')
            weaviate_port = int(os.environ.get('WEAVIATE_PORT'))
            cluster_url = f"http://{weaviate_host}:{weaviate_port}"
        vector_store_config = {
            "collection_name": "openmemory",
            "cluster_url": cluster_url
        }
    elif os.environ.get('REDIS_URL'):
        vector_store_provider = "redis"
        vector_store_config = {
            "collection_name": "openmemory",
            "redis_url": os.environ.get('REDIS_URL')
        }
    elif os.environ.get('PG_HOST') and os.environ.get('PG_PORT'):
        vector_store_provider = "pgvector"
        vector_store_config.update({
            "host": os.environ.get('PG_HOST'),
            "port": int(os.environ.get('PG_PORT')),
            "dbname": os.environ.get('PG_DB', 'mem0'),
            "user": os.environ.get('PG_USER', 'mem0'),
            "password": os.environ.get('PG_PASSWORD', 'mem0')
        })
    elif os.environ.get('MILVUS_HOST') and os.environ.get('MILVUS_PORT'):
        vector_store_provider = "milvus"
        milvus_host = os.environ.get('MILVUS_HOST')
        milvus_port = int(os.environ.get('MILVUS_PORT'))
        milvus_url = f"http://{milvus_host}:{milvus_port}"
        vector_store_config = {
            "collection_name": "openmemory",
            "url": milvus_url,
            "token": os.environ.get('MILVUS_TOKEN', ''),
            "db_name": os.environ.get('MILVUS_DB_NAME', ''),
            "metric_type": "COSINE"
        }
    elif os.environ.get('ELASTICSEARCH_HOST') and os.environ.get('ELASTICSEARCH_PORT'):
        vector_store_provider = "elasticsearch"
        elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST')
        elasticsearch_password = os.environ.get('ELASTICSEARCH_PASSWORD')
        if not elasticsearch_password:
            raise RuntimeError("ELASTICSEARCH_PASSWORD is required when Elasticsearch vector store is selected.")
        elasticsearch_scheme = "https" if os.environ.get('ELASTICSEARCH_USE_SSL', 'true').lower() == 'true' else "http"
        vector_store_config.update({
            "host": f"{elasticsearch_scheme}://{elasticsearch_host}",
            "port": int(os.environ.get('ELASTICSEARCH_PORT')),
            "user": os.environ.get('ELASTICSEARCH_USER', 'elastic'),
            "password": elasticsearch_password,
            "verify_certs": os.environ.get('ELASTICSEARCH_VERIFY_CERTS', 'true').lower() == 'true',
            "use_ssl": os.environ.get('ELASTICSEARCH_USE_SSL', 'true').lower() == 'true',
        })
    elif os.environ.get('OPENSEARCH_HOST') and os.environ.get('OPENSEARCH_PORT'):
        vector_store_provider = "opensearch"
        vector_store_config.update({
            "host": os.environ.get('OPENSEARCH_HOST'),
            "port": int(os.environ.get('OPENSEARCH_PORT')),
            "user": os.environ.get('OPENSEARCH_USER', 'admin'),
            "password": os.environ.get('OPENSEARCH_PASSWORD'),
            "verify_certs": os.environ.get('OPENSEARCH_VERIFY_CERTS', 'true').lower() == 'true',
            "use_ssl": os.environ.get('OPENSEARCH_USE_SSL', 'true').lower() == 'true',
        })
    elif os.environ.get('FAISS_PATH'):
        vector_store_provider = "faiss"
        vector_store_config = {
            "collection_name": "openmemory",
            "path": os.environ.get('FAISS_PATH'),
            "distance_strategy": "cosine"
        }
    else:
        vector_store_provider = "qdrant"
        vector_store_config.update({
            "host": qdrant_host,
            "port": int(qdrant_port),
        })
        if qdrant_is_external:
            if os.environ.get("QDRANT_URL"):
                vector_store_config = {
                    "collection_name": "openmemory",
                    "url": os.environ.get("QDRANT_URL"),
                }
            else:
                vector_store_config.update({
                    "host": qdrant_host,
                    "port": int(qdrant_port),
                })
            if os.environ.get("QDRANT_API_KEY"):
                vector_store_config["api_key"] = os.environ.get("QDRANT_API_KEY")

    embedding_model_dims = _get_embedding_model_dims()
    if embedding_model_dims is not None and vector_store_provider not in {"chroma", "weaviate"}:
        vector_store_config["embedding_model_dims"] = embedding_model_dims

    print(f"Auto-detected vector store: {vector_store_provider}")
"""
memory_text = replace_between_required(
    memory_text,
    vector_start,
    vector_end,
    vector_block + vector_end,
    "vector store detection",
)
memory.write_text(memory_text)

require_contains(memory_text, "qdrant_is_external", "external Qdrant detection")
require_contains(memory_text, "REDIS_URL", "Redis vector-store detection")

mcp_server = Path("/app/api/app/mcp_server.py")
mcp_server.write_text(
    replace_required(
        mcp_server.read_text(),
        "                limit=10, \n",
        "                top_k=10, \n",
        "MCP search uses Mem0 top_k",
    )
)

categorization = Path("/app/api/app/utils/categorization.py")
categorization_text = replace_required(
    categorization.read_text(),
    "import logging\nfrom typing import List\n",
    "import logging\nimport os\nfrom typing import List\n",
    "categorization imports os",
)
categorization_text = replace_required(
    categorization_text,
    "openai_client = OpenAI()\n",
    """openai_client = None


def _get_openai_client():
    global openai_client
    if openai_client is not None:
        return openai_client
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_ADMIN_KEY")):
        logging.info("[INFO] Skipping memory categorization because no OpenAI credential is configured.")
        return None
    openai_client = OpenAI()
    return openai_client
""",
    "lazy OpenAI categorization client",
)
categorization_text = replace_required(
    categorization_text,
    "    try:\n        messages = [",
    "    completion = None\n    try:\n        client = _get_openai_client()\n        if client is None:\n            return []\n\n        messages = [",
    "optional categorization client guard",
)
categorization_text = replace_required(
    categorization_text,
    "        completion = openai_client.beta.chat.completions.parse(",
    "        completion = client.beta.chat.completions.parse(",
    "categorization client call",
)
categorization.write_text(categorization_text)
