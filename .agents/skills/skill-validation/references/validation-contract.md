# Skill Validation Contract

## Canonical structure

- A canonical router is `.agents/skills/<lowercase-kebab-name>/SKILL.md` with matching `name` frontmatter,
  a `Use when...` description, exactly one H1, direct links to every local topical reference, and an
  evaluation-case matrix that lists those references exactly.
- Reference links must be normalized, local, case-correct, contained in the canonical catalog, and directly
  reachable from the router. Keep topical references distinct, concise, and below the validator's size limits.
- Use existing focused skills instead of creating overlapping ones. Preserve useful source coverage through the
  audited inventory, content-coverage destinations, manifest hashes, and generated host adapters.

## Change and verification contract

- Write a failing validator or evaluation test before changing generator or validator behavior.
- Keep generated Claude and Copilot adapters generated; change their canonical sources and run the synchronizers.
- Every router must directly expose the shared [Final Verification](final-verification.md) contract. Route, page,
  template, controller, layout, asset, modal, and interactive UI skills must require controlled in-app browser
  rendering, with the authenticated `dev`/`test` Diagnostic GET/CSRF-protected POST fallback explicitly available
  when the browser controller cannot reach `app_hublist.test`. It is not a production substitute or an
  unauthenticated raw HTTP check.
- Run the focused test, audit, validator, generated-file check, manifest check, and `git diff --check`; use the
  final verification contract immediately before claiming the task complete.
