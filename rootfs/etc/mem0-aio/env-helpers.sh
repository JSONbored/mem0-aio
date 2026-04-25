#!/usr/bin/env bash
# shellcheck shell=bash

_mem0_is_local_qdrant_host() {
	case "${1:-127.0.0.1}" in
	127.0.0.1 | localhost | "")
		return 0
		;;
	*)
		return 1
		;;
	esac
}

_mem0_vector_store_candidates() {
	local candidates=()

	if [[ -n ${CHROMA_HOST-} ]] || [[ -n ${CHROMA_PORT-} ]]; then
		candidates+=(chroma)
	fi
	if [[ -n ${WEAVIATE_CLUSTER_URL-} ]] || [[ -n ${WEAVIATE_HOST-} ]] || [[ -n ${WEAVIATE_PORT-} ]]; then
		candidates+=(weaviate)
	fi
	if [[ -n ${REDIS_URL-} ]]; then
		candidates+=(redis)
	fi
	if [[ -n ${PG_HOST-} ]] || [[ -n ${PG_PORT-} ]] || [[ -n ${PG_DB-} ]] || [[ -n ${PG_USER-} ]] || [[ -n ${PG_PASSWORD-} ]]; then
		candidates+=(pgvector)
	fi
	if [[ -n ${MILVUS_HOST-} ]] || [[ -n ${MILVUS_PORT-} ]] || [[ -n ${MILVUS_TOKEN-} ]] || [[ -n ${MILVUS_DB_NAME-} ]]; then
		candidates+=(milvus)
	fi
	if [[ -n ${ELASTICSEARCH_HOST-} ]] || [[ -n ${ELASTICSEARCH_PORT-} ]] || [[ -n ${ELASTICSEARCH_USER-} ]] || [[ -n ${ELASTICSEARCH_PASSWORD-} ]]; then
		candidates+=(elasticsearch)
	fi
	if [[ -n ${OPENSEARCH_HOST-} ]] || [[ -n ${OPENSEARCH_PORT-} ]] || [[ -n ${OPENSEARCH_USER-} ]] || [[ -n ${OPENSEARCH_PASSWORD-} ]]; then
		candidates+=(opensearch)
	fi
	if [[ -n ${FAISS_PATH-} ]]; then
		candidates+=(faiss)
	fi
	if [[ -n ${QDRANT_URL-} ]] || [[ -n ${QDRANT_API_KEY-} ]] || ! _mem0_is_local_qdrant_host "${QDRANT_HOST:-127.0.0.1}"; then
		candidates+=(qdrant)
	fi

	printf '%s\n' "${candidates[@]}"
}

mem0_validate_vector_store_config() {
	local candidates=()
	local candidate
	# shellcheck disable=SC2312
	while IFS= read -r candidate; do
		[[ -n ${candidate} ]] && candidates+=("${candidate}")
	done < <(_mem0_vector_store_candidates)

	if ((${#candidates[@]} > 1)); then
		printf 'mem0-aio configuration error: choose exactly one vector store backend; found %s.\n' "${candidates[*]}" >&2
		printf 'Set only one of QDRANT_*, REDIS_URL, PG_*, CHROMA_*, WEAVIATE_*, MILVUS_*, ELASTICSEARCH_*, OPENSEARCH_*, or FAISS_PATH.\n' >&2
		return 1
	fi

	if [[ -n ${CHROMA_HOST-} || -n ${CHROMA_PORT-} ]] && [[ -z ${CHROMA_HOST-} || -z ${CHROMA_PORT-} ]]; then
		printf 'mem0-aio configuration error: Chroma requires both CHROMA_HOST and CHROMA_PORT.\n' >&2
		return 1
	fi

	if [[ -z ${WEAVIATE_CLUSTER_URL-} ]] && [[ -n ${WEAVIATE_HOST-} || -n ${WEAVIATE_PORT-} ]] && [[ -z ${WEAVIATE_HOST-} || -z ${WEAVIATE_PORT-} ]]; then
		printf 'mem0-aio configuration error: Weaviate requires WEAVIATE_CLUSTER_URL or both WEAVIATE_HOST and WEAVIATE_PORT.\n' >&2
		return 1
	fi

	if [[ -n ${PG_HOST-} || -n ${PG_PORT-} || -n ${PG_DB-} || -n ${PG_USER-} || -n ${PG_PASSWORD-} ]] && [[ -z ${PG_HOST-} || -z ${PG_PORT-} ]]; then
		printf 'mem0-aio configuration error: PGVector requires at least PG_HOST and PG_PORT when any PG_* override is set.\n' >&2
		return 1
	fi

	if [[ -n ${MILVUS_HOST-} || -n ${MILVUS_PORT-} || -n ${MILVUS_TOKEN-} || -n ${MILVUS_DB_NAME-} ]] && [[ -z ${MILVUS_HOST-} || -z ${MILVUS_PORT-} ]]; then
		printf 'mem0-aio configuration error: Milvus requires at least MILVUS_HOST and MILVUS_PORT when any MILVUS_* override is set.\n' >&2
		return 1
	fi

	if [[ -n ${ELASTICSEARCH_HOST-} || -n ${ELASTICSEARCH_PORT-} || -n ${ELASTICSEARCH_USER-} || -n ${ELASTICSEARCH_PASSWORD-} ]] && [[ -z ${ELASTICSEARCH_HOST-} || -z ${ELASTICSEARCH_PORT-} ]]; then
		printf 'mem0-aio configuration error: Elasticsearch requires at least ELASTICSEARCH_HOST and ELASTICSEARCH_PORT when any Elasticsearch host or credential override is set.\n' >&2
		return 1
	fi

	if [[ -n ${OPENSEARCH_HOST-} || -n ${OPENSEARCH_PORT-} || -n ${OPENSEARCH_USER-} || -n ${OPENSEARCH_PASSWORD-} ]] && [[ -z ${OPENSEARCH_HOST-} || -z ${OPENSEARCH_PORT-} ]]; then
		printf 'mem0-aio configuration error: OpenSearch requires at least OPENSEARCH_HOST and OPENSEARCH_PORT when any OpenSearch host or credential override is set.\n' >&2
		return 1
	fi

	if [[ -n ${QDRANT_API_KEY-} && -z ${QDRANT_URL-} ]] && _mem0_is_local_qdrant_host "${QDRANT_HOST:-127.0.0.1}"; then
		printf 'mem0-aio configuration error: QDRANT_API_KEY requires QDRANT_URL or an external QDRANT_HOST. The bundled Qdrant service is not started with API-key auth.\n' >&2
		return 1
	fi

	if [[ -n ${QDRANT_URL-} ]] && ! _mem0_is_local_qdrant_host "${QDRANT_HOST:-127.0.0.1}"; then
		printf 'mem0-aio configuration error: set QDRANT_URL or external QDRANT_HOST/QDRANT_PORT, not both.\n' >&2
		return 1
	fi
}

mem0_uses_external_vector_store() {
	local candidates=()
	local candidate
	# shellcheck disable=SC2312
	while IFS= read -r candidate; do
		[[ -n ${candidate} ]] && candidates+=("${candidate}")
	done < <(_mem0_vector_store_candidates)
	((${#candidates[@]} > 0))
}
