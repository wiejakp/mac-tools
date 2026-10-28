#!/bin/sh
set -eu
repo_dir=$(cd -P -- "$(dirname -- "$0")/.." >/dev/null && pwd -P)
exec "$repo_dir/mount-cch.sh" "$@"
