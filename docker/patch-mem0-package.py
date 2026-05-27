from pathlib import Path


def replace_required(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Mem0 package patch anchor not found: {label}")
    return text.replace(old, new, 1)


site_packages = sorted(Path("/opt/venv/lib").glob("python*/site-packages"))
if not site_packages:
    raise RuntimeError("Unable to locate runtime site-packages")

elasticsearch_store = site_packages[0] / "mem0" / "vector_stores" / "elasticsearch.py"
elasticsearch_store.write_text(
    replace_required(
        elasticsearch_store.read_text(),
        "        bulk(self.client, actions)\n",
        "        bulk(self.client, actions, refresh=True)\n",
        "Elasticsearch vector bulk insert",
    )
)
