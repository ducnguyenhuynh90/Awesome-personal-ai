---
name: skill-author
description: Proposes a new or patched SKILL.md as a PR for David to approve. Use when the same kind of request has come up 3+ times in 30 days with no skill for it, or a skill keeps failing review.
metadata:
  department: staff
  tags:
  - new skill
  - create skill
  - improve skill
  - skill gap
  - recurring task
  examples:
  - We keep doing affiliate payout checks by hand — make a skill
  - The campaign-brief skill keeps missing budget — fix it
  writes_to:
  - .claude/skills/
---

# skill-author

Proposes a new or patched SKILL.md as a PR for David to approve.

## Steps

1. Collect the 3+ traces or the failing reviews as evidence.
2. Copy the structure of an existing skill: frontmatter (name, description with 'Use when', metadata.department/tags/examples) + Steps, Output, Quality checks, Pitfalls.
3. Add ≥ 2 routing examples and add them to evals/routing/cases.yaml in the PR description (David commits evals).
4. Run `robin validate` and `robin eval routing` — both must pass.
5. Open a branch + PR; never merge.

## Output

PR with the SKILL.md diff, the evidence links and the eval result.

## Quality checks

- Validate passes.
- Routing eval does not regress.

## Pitfalls (learned)

- Writing a skill for a one-off task.
