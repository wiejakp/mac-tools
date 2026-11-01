---
name: skill-validation
description: "Use when creating, migrating, validating, or auditing repository AI skills."
---

# Skill Validation

Validate canonical skills as executable routing contracts, not as file-preservation wrappers.

## Workflow

1. Write a failing validator or evaluation case for the defect before changing skill content.
2. Read [Skill Validation Contract](references/validation-contract.md).
3. Read [Final Verification](references/final-verification.md) before the final implementation gate.
4. Validate frontmatter, direct topical routing, normalized contained links, case, orphans, duplicate purposes, scripts/assets, evaluations, and complete classified source coverage.
5. Run the repository audit, validator, generated-file check, tests, and final structural searches.

## Verification

Use [evaluation cases](references/evaluation-cases.json) to verify activation, expected references, forbidden references, and failure recovery.

## Common Mistakes

- Accepting a valid link while leaving an orphaned or monolithic reference.
- Marking source content covered without an existing final destination and line-complete audit record.
