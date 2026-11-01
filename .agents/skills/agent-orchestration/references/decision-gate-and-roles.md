# Decision Gate and Worker Roles

Use one agent unless the current user explicitly authorizes delegation.
A small native-command/configuration change normally stays inline.

Before any authorized dispatch, verify every condition:

1. The exact subtask is covered by the current authorization.
2. It has an independent outcome, file ownership and runtime state.
3. It can return a bounded result without nested delegation.
4. Its expected benefit exceeds coordination and review cost.
5. Its data stays with the selected assistant service; another provider or cloud
   worker requires separate destination-specific permission.

The main agent retains shared files, architecture, security decisions, integration
and the final `make verify` result. Workers run only their assigned focused checks.
Do not create automatic explorer/architect/reviewer/tester stages.

Give concurrent write workers separate worktrees and disjoint file ownership.
Prove independent temporary paths, locks, ports and other shared state before
parallel verification. Otherwise serialize the work.

Choose only models and controls actually offered by the client, within user
preferences. Do not hardcode a model family, reasoning tier or cost estimate.

Cancel owned workers that exceed scope, duplicate completed work or cease to
help. Preserve their changes for review; never terminate unrelated sessions.
