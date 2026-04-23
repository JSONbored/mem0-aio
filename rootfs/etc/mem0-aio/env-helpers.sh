#!/usr/bin/env bash
# shellcheck shell=bash

mem0_uses_external_vector_store() {
	if [[ -n ${CHROMA_HOST-} ]] || [[ -n ${WEAVIATE_CLUSTER_URL-} ]] ||
		[[ -n ${WEAVIATE_HOST-} ]] || [[ -n ${REDIS_URL-} ]] ||
		[[ -n ${PG_HOST-} ]] || [[ -n ${MILVUS_HOST-} ]] ||
		[[ -n ${ELASTICSEARCH_HOST-} ]] || [[ -n ${OPENSEARCH_HOST-} ]] ||
		[[ -n ${FAISS_PATH-} ]]; then
		return 0
	fi

	case "${QDRANT_HOST:-127.0.0.1}" in
	127.0.0.1 | localhost | "")
		return 1
		;;
	*)
		return 0
		;;
	esac
}
