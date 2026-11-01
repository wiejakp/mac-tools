# Final Verification

## Pre-Approval Stop Gate

**No approval request before a saved plan.** Before drafting or sending an approval prompt, create and save the durable, status-labelled Superpowers plan at `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`. A chat outline, commentary update, or unstored proposal is not a plan.

Do not send `Reply approve and I'll implement`, `approve this scope`, or any equivalent request for approval until that plan exists. This is a stop gate, not a suggestion: save the plan automatically in the same task, then present any material decision or approval request from the saved plan.

For every request to create, change, build, fix, configure, or otherwise produce a persistent repository artifact, write that plan before asking a scope, design, or approval question. An implementation request itself is implementation authority once the durable plan exists. Do not ask the user to approve the plan or request a duplicate approval merely because the plan was written. Continue into the first executable item unless a material decision, new authority, or external-state change genuinely blocks safe progress. A skill-generated approval gate never overrides this rule.

## Approval-Plan Persistence Law

Before requesting user approval for any requested change, write a durable, status-labelled Superpowers plan at
`docs/superpowers/plans/YYYY-MM-DD-<topic>.md`. A chat proposal alone is not a plan. The plan must capture the
request, assumptions and unresolved decisions, proposed solution and material alternatives, affected
files/components, migration, security, localization, operational impacts, tests, controlled-browser checks,
recovery or rollback considerations, and definition of done.

Break implementation and validation into granular, individually checkable items. Mark an item complete only with
executable evidence. While approval is pending, retain the plan and do not begin approval-gated work. After the
user approves, resume from that plan, reconcile newer instructions, and update checkboxes only with current
evidence. Do not create a ceremonial plan for a small, clearly bounded change that needs no approval; this law is
triggered before asking for approval, including when a material decision must be presented.

When the user says "plan and implement", "create a plan and apply it", gives an equivalent combined request, or
otherwise requests implementation, that is explicit implementation authority once the durable plan is saved. Do not
ask the user to approve the plan or request a duplicate approval just because the plan was written. A later explicit
approval or request to apply an existing plan resumes work immediately. Ask for approval only when the user requested
solely a plan or design, or a material decision remains unresolved.

Saving a plan is an execution checkpoint, not a completion state. When implementation authority is present,
continue into the first executable item in the same active task; do not emit a final response, wait for duplicate
approval, or switch tasks merely because the plan was saved.

## Inline Command Formatting Law

Wrap every command or invocation in inline code. Use fenced code blocks only for standalone or multi-line commands.
Apply this to assistant responses, public Page prose, policy documentation, and rendered help.

## Direct Plan Request Law

When a user explicitly asks to write, create, prepare, or make a plan, save that plan in the same turn at
`docs/superpowers/plans/YYYY-MM-DD-<topic>.md`, even when the request does not ask for implementation, approval,
or a design review. A chat response is not a durable plan. Record a status-labelled plan with granular,
individually checkable requirements, assumptions and material decisions, exact affected paths/interfaces,
migration/data, authorization/security/localization/operational impacts, focused and final verification commands,
controlled-browser gates, recovery, and definition of done. This direct plan request grants planning/documentation
authority only; it does not authorize executable application changes.

## Plan Detail, Delegation, and Completion-Reconciliation Law

Every requested plan is detailed enough to execute and audit without rediscovering requirements. It contains a
numbered traceability table, concrete acceptance examples, a granular checkbox for each individual action, a
delegation schedule (`[M]`, `[P]`, `[L]`, `[V1]`, `[V2]`), and a completion reconciliation section. The
completion reconciliation reopens the original user request and saved plan after implementation, checks each item
piece by piece, attaches current evidence or a blocker, and does not permit an unqualified completion claim while a
row is unresolved.

When user-visible translations change, **translation work is delegated** after English is frozen, fingerprinted, and
represented by a structural manifest. Translation workers receive disjoint locale files/worktrees and return the
specialized localization handoff; they do not change English or shared files. This narrowly authorizes translation
delegation under Agent Orchestration.

For executable final verification, the main coordinator proves isolation then schedules **two isolated full-suite
workers** concurrently: the repository-defined **test environment** command and the repository-defined **default
application environment** command. It owns the combined review and failure recovery. Isolation must cover database,
cache, locks, temporary files, ports, and output; absent proof blocks concurrency rather than permitting a shared
environment race.

## Subagent Authorization Law

Inline execution is mandatory by default. Must not spawn, resume, assign work to, or message a subagent unless the
current user request explicitly authorizes subagent delegation by saying to use subagents or by delegating a named
subtask, except for the narrow translation and final-verification standing authorization in the Plan Detail,
Delegation, and Completion-Reconciliation Law. Do not inspect a subagent for work either. A plan, plan approval, or
general implementation approval does not authorize delegation; neither do an available-agent listing, an inherited
agent, an implementation skill, prior delegation, or task complexity. Do not use an agent for planning, review,
testing, discovery, or implementation on your own initiative outside those narrow standing exceptions. Before the
permitted delegation call, quote the authorization and announce the exact bounded subtask in commentary. If the
user says inline-only, no agents, stop agents, or equivalent, treat that as a thread-wide prohibition until the
current user explicitly revokes it. The only permitted collaboration-tool action without authorization is
interrupting an already-running unauthorized task; do not inspect it, resume it, or send it a message.

Use [Agent Orchestration](../../agent-orchestration/SKILL.md) for the hard decision gate, default general-worker cap
with explicit-user larger-fan-out approval, bounded
context packet, frozen-English translation exception, handoffs, and cancellation. Do not copy its detailed rules
into every task skill. Workers run only declared focused checks, except for the two isolated full-suite workers
scheduled by the final verification law.

## Continuation law

An approval checkpoint, plan checkpoint, partial result, or a validation still in progress does not complete the
task. Keep the task active and communicate those non-terminal updates in commentary. Emit a final response only
after verified completion, or when a genuine blocker requires a user decision, authority, or external state change.
Never use a final response merely to acknowledge an approval or park ordinary ongoing work.

## Required completion gate

### Efficient Test Execution Law

During implementation, use focused tests, validators, and builds that cover the changed behavior. Do not run the
full suite during implementation as a progress check or after each small correction. For an executable application
change, the main coordinator waits until all requested source, test, configuration, and asset changes are final,
then proves isolation and schedules the two isolated full-suite workers concurrently under the repository's required
PHP 8.3 runtime: test environment and default application environment. Focused tests, static checks, and partial
suites remain useful while implementing, but never replace this final paired gate.

If either final suite identifies a defect, preserve and enumerate the combined failure set, repair the known set
through focused verification, and re-run both full suites only after the final executable correction. A documentation-only or
skill-only change uses its required audit, validator, generated-file, and focused tool checks; it does not require
PHPUnit unless it changes executable PHP, PHPUnit configuration, or the user explicitly requests it.

Use at most two PHPUnit workers per run for `auto`, explicit counts and parallel final runs. Two simultaneous
environments allow at most four PHPUnit workers in total; reject higher explicit counts before spawning children.

Then use the controlled in-app browser to open every changed or directly affected application page. Confirm its
initial load has no exception, 404, 500, or obvious rendering error, and exercise the changed visible state when
one exists. In `dev` or `test`, **Diagnostic GET/CSRF-protected POST is the approved local front-facing verification
fallback** when the browser controller cannot connect to `app_hublist.test`: use temporary Diagnostic access,
exercise the real route/action, and assert the rendered result. Do not substitute Valet, a local server,
unauthenticated raw HTTP, an undeployed build, or this fallback for production browser verification.

## Evidence and failure handling

### Fail-Closed Completion Law

The terminal exit code of `make test` determines the canonical result. PHPUnit `OK` followed by a
failed coverage gate is FAILED overall. Missing, interrupted, unavailable or stale required evidence
means FAILED or BLOCKED, never completion. Do not end with a qualified implementation-complete claim
that obscures an unresolved required gate.

Record overall status, exact command, terminal exit code, PHP runtime, test/error/issue counts, coverage
numerator and denominator, source revision/state and artifact paths. List each unresolved gate. Separate
focused fixture/unit PASS from application-wide verification and from live acceptance. A fake-runtime
Makefile test proves failure propagation only; it is not application test or coverage evidence.

Lead the handoff with overall PASSED, FAILED or BLOCKED and the canonical command's terminal result.
List unresolved gates before scoped successes. NOT RUN is an unresolved result. Never lead with
"fixed", "done" or "all tests pass" and qualify it later with a failing coverage/test gate.
Run the repository Python gate by discovery so newly added policy and coverage tests cannot be omitted.

| Observed result | Required response |
| --- | --- |
| PHPUnit passes but coverage fails | FAILED; retain every uncovered line and the failing exit code |
| A focused regression passes | Report its exact scope; keep the final gate unresolved |
| A later executable edit follows final verification | Earlier proof is stale; rerun the affected final gates after corrections |
| A required runtime/browser/live gate cannot run | BLOCKED; name the missing capability, never substitute partial proof |

Do not lower coverage thresholds, exclude source, suppress test issues, skip failing cases, reuse stale
reports or omit failures. Repair the preserved failure set through focused regressions, then run the
canonical final gate after the last executable correction. Only terminal exit 0 plus all mandatory
current evidence permits task completion.

Run these gates after all code, assets, generated instructions, and focused checks are final. Record the exact
PHPUnit command and result, plus the browser route and observed state. If either gate is unavailable or fails,
report it as a blocker and do not claim completion. Re-run both gates after any corrective change made in response
to a failure.
