#!/bin/sh
# Finder launcher for the logs-only tool.
set -eu
repo_dir=$(cd -P -- "$(dirname -- "$0")/.." >/dev/null && pwd -P)
exec "$repo_dir/clear-logs.sh" "$@"
