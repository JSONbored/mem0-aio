#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:-.}"
strict_placeholders="${STRICT_PLACEHOLDERS:-false}"

args=(validate-derived --repo-path "${repo_root}")
if [[ ${strict_placeholders} == "true" ]]; then
	args+=(--strict-placeholders)
fi

if python3 -c "import aio_fleet" >/dev/null 2>&1; then
	exec python3 -m aio_fleet.cli "${args[@]}"
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
candidate_roots=()
if [[ -n ${AIO_FLEET_PATH-} ]]; then
	candidate_roots+=("${AIO_FLEET_PATH}")
fi
candidate_roots+=(
	"${script_dir}/../../aio-fleet"
	"${script_dir}/../../../aio-fleet"
	"../aio-fleet"
	"../../aio-fleet"
)

for candidate in "${candidate_roots[@]}"; do
	if [[ -d ${candidate}/src/aio_fleet ]]; then
		PYTHONPATH="${candidate}/src${PYTHONPATH:+:${PYTHONPATH}}" exec python3 -m aio_fleet.cli "${args[@]}"
	fi
done

cat >&2 <<'EOF'
template validation error: aio-fleet is required for derived repo validation.
Install aio-fleet or set AIO_FLEET_PATH to a local aio-fleet checkout.
EOF
exit 1
