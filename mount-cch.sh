#!/bin/sh
# Mount the CCH work SMB drive only.
set -eu
script_dir=$(cd -P -- "$(dirname -- "$0")" >/dev/null && pwd -P)
exec /usr/bin/python3 -u "$script_dir/src/local_scripts/network_mounts.py" "$@" --profile work
