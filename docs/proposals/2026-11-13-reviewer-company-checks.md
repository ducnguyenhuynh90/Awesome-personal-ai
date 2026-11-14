# Proposal: company checks for the reviewer (David approves)

Status: APPROVED by David 2026-11-13 ("go reviewer") and applied to .claude/agents/reviewer.md and .claude/skills/review-rubric/SKILL.md.

`.claude/agents/reviewer.md` and `.claude/skills/review-rubric/` are the verifier, which CLAUDE.md reserves for David.
The other 13 agents now carry the company way of working (#BeClear, #Context, #DontPassMessage, escalate with a
recommendation, labelled assumptions). For the reviewer to enforce it, add to the rubric:

- FAIL if the output is not #BeClear (specific, short, simple, obvious), or a number lacks #Context
  (Number · Share · Anchor · Meaning).
- FAIL if an assumption is presented as fact, or the output reads as unreviewed AI output.
- FAIL if a recommendation does not name the company priority metric it moves.
- FAIL if company facts, numbers or names appear in a file meant for this public repo.


