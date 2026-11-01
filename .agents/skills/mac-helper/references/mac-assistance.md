# Local Mac assistance

`agent-setup.sh --inventory` observes only OS/build, architecture, hardware model,
RAM, and the agent/tool executables relevant to this setup. With `--yes`, it saves
`config/mac-helper.local.json`, which must remain ignored. Recheck volatile facts
when they matter. Omit serial numbers, UUIDs, hostnames, network addresses,
account inventories, credentials, browser history, and broad filesystem listings.

Start with the smallest read-only diagnostic that answers the user's symptom.
Expand access only for named paths within the user's task. Cloud storage remains
excluded. Installed tools may need separate permissions; do not bypass a denial
using another tool. Do not inspect files inside work or home network shares.

For this project's cleaners, use their documented `--dry-run` only when requested;
never run a real cleanup to test code. Keep logs and cache cleanup separate.
For mounts, use simulated test connections; never list mounted share contents.
For any change here, run `make verify` and report real limitations.
