#!/usr/bin/env bash
set -euo pipefail

apt_root="${1:-/}"
apt_root="${apt_root%/}"
apt_dir="${apt_root}/etc/apt"

if [[ ! -d ${apt_dir} ]]; then
	echo "apt directory not found: ${apt_dir}" >&2
	exit 1
fi

if grep -RqsE '(^|[[:space:]])(Trusted:[[:space:]]*yes|Allow-Insecure:[[:space:]]*yes|Allow-Downgrade-To-Insecure:[[:space:]]*yes|trusted=yes|allow-insecure=yes|allow-downgrade-to-insecure=yes)([[:space:]]|$)' "${apt_dir}"; then
	echo "insecure apt source option is not allowed" >&2
	exit 1
fi

source_files="$(mktemp)"
trap 'rm -f "${source_files}"' EXIT
find "${apt_dir}" -type f \( -name '*.list' -o -name '*.sources' \) -print0 >"${source_files}"

while IFS= read -r -d '' source_file; do
	perl -0pi -e '
        s{http://archive\.ubuntu\.com/ubuntu/}{https://archive.ubuntu.com/ubuntu/}g;
        s{http://security\.ubuntu\.com/ubuntu/}{https://security.ubuntu.com/ubuntu/}g;
        s{http://ports\.ubuntu\.com/ubuntu-ports/}{https://ports.ubuntu.com/ubuntu-ports/}g;
    ' "${source_file}"
done <"${source_files}"

apt_source_uris="$(
	find "${apt_dir}" -type f \( -name '*.list' -o -name '*.sources' \) -exec awk '
        $1 == "URIs:" { for (i = 2; i <= NF; i++) print $i }
        $1 == "deb" || $1 == "deb-src" {
            for (i = 2; i <= NF; i++) {
                if ($i ~ /^https?:\/\//) { print $i; break }
            }
        }
    ' {} +
)"

for uri in ${apt_source_uris}; do
	case "${uri}" in
	https://archive.ubuntu.com/ubuntu/ | https://security.ubuntu.com/ubuntu/ | https://ports.ubuntu.com/ubuntu-ports/) ;;
	http://*)
		echo "plaintext apt source remained: ${uri}" >&2
		exit 1
		;;
	*)
		echo "unsupported apt source: ${uri}" >&2
		exit 1
		;;
	esac
done
