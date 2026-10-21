#!/bin/sh
# Application logs only. Double-click for the menu, or pass --dry-run / --yes.
set -eu
script_dir=$(cd -P -- "$(dirname -- "$0")" >/dev/null && pwd -P)
exec /usr/bin/python3 -u "$script_dir/src/local_scripts/sites_cleaner.py" "$@" --kind logs
