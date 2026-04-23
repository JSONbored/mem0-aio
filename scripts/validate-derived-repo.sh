#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:-.}"
cd "${repo_root}"
strict_placeholders="${STRICT_PLACEHOLDERS:-false}"

fail() {
	echo "template validation error: $*" >&2
	exit 1
}

require_file() {
	local path="$1"
	[[ -f ${path} ]] || fail "missing required file: ${path}"
}

require_absent() {
	local path="$1"
	[[ ! -e ${path} ]] || fail "remove template placeholder path in derived repo: ${path}"
}

check_no_placeholder() {
	local pattern="$1"
	shift
	if grep -F -n -- "${pattern}" "$@" >/dev/null 2>&1; then
		fail "found unresolved placeholder '${pattern}' in: $*"
	fi
}

require_file "Dockerfile"
require_file "README.md"
require_file "pyproject.toml"
require_file "scripts/ci_flags.py"
require_file "tests/unit/test_ci_flags.py"
require_file "tests/template/test_validate_template.py"
require_file "tests/integration/test_container_runtime.py"
require_file "scripts/validate-template.py"
require_file "scripts/update-template-changes.py"
require_file ".github/FUNDING.yml"
require_file "SECURITY.md"
require_file ".github/pull_request_template.md"
require_file ".github/ISSUE_TEMPLATE/bug_report.yml"
require_file ".github/ISSUE_TEMPLATE/feature_request.yml"
require_file ".github/ISSUE_TEMPLATE/installation_help.yml"
require_file ".github/ISSUE_TEMPLATE/config.yml"
require_file "renovate.json"
require_absent ".github/CODEOWNERS"

effective_template_xml="${TEMPLATE_XML-}"
if [[ -z ${effective_template_xml} ]]; then
	repo_name="${PWD##*/}"
	inferred_repo_xml="${repo_name}.xml"
	if [[ -f ${inferred_repo_xml} ]]; then
		effective_template_xml="${inferred_repo_xml}"
	else
		root_xml_files=()
		shopt -s nullglob
		for xml_path in ./*.xml; do
			[[ -f ${xml_path} ]] || continue
			root_xml_files+=("${xml_path#./}")
		done
		shopt -u nullglob
		if [[ ${#root_xml_files[@]} -eq 1 ]]; then
			effective_template_xml="${root_xml_files[0]}"
		fi
	fi
fi

is_template_repo="false"
if [[ -f .github/workflows/publish-release.yml ]] && grep -F -q -- "Publish Release / Template" .github/workflows/publish-release.yml; then
	is_template_repo="true"
fi

if [[ -n ${effective_template_xml} ]]; then
	require_file "${effective_template_xml}"
	if [[ ${is_template_repo} != "true" ]]; then
		require_absent "template-aio.xml"
	fi
fi

xml_files=()
if [[ -n ${effective_template_xml} ]] && [[ -f ${effective_template_xml} ]]; then
	xml_files+=("${effective_template_xml}")
fi

if [[ ${strict_placeholders} == "true" ]]; then
	check_no_placeholder "Replace this starter base with the real upstream image once the derived repo is wired." "Dockerfile"
	if [[ ${#xml_files[@]} -gt 0 ]]; then
		check_no_placeholder "yourapp-aio" "${xml_files[@]}"
		check_no_placeholder "Replace this overview with the real app description and first-run guidance." "${xml_files[@]}"
		check_no_placeholder "replace-with-real-search-terms" "${xml_files[@]}"
		check_no_placeholder "Replace this with any real operational prerequisites or remove it." "${xml_files[@]}"
		check_no_placeholder "https://github.com/JSONbored/yourapp-aio/releases" "${xml_files[@]}"
	fi
	check_no_placeholder "aio-template starter app" rootfs/etc/services.d/app/run rootfs/usr/local/bin/aio-template-app.py
fi

echo "Derived repo validation passed."
