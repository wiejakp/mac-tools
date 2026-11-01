#!/bin/sh
# Preview or apply explicitly selected local agent configuration repairs.
set -eu
script_dir=$(cd -P -- "$(dirname -- "$0")" >/dev/null && pwd -P)
exec /usr/bin/python3 -B "$script_dir/src/local_scripts/agent_setup.py" "$@"
