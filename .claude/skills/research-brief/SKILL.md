---
name: research-brief
description: General web/desk research that returns a sourced, decision-oriented answer. Use when a question needs desk research and no more specific skill (market-scan, competitor-teardown, account-research) fits.
metadata:
  department: shared
  tags:
  - research
  - find out
  - look up
  - investigate
  - background
  - overview
  - what is
  examples:
  - What are the main buy-now-pay-later players in Southeast Asia?
  - Find out how other companies run AI agent teams
  writes_to:
  - knowledge/
---

# research-brief

General web/desk research that returns a sourced, decision-oriented answer.

## Steps

1. Restate the decision the research serves in one line (if unclear, ask one question).
2. Run the kb `query` tool first; reuse fresh knowledge instead of re-researching.
3. Search; open at most 5 sources; grade each with source-grading.
4. Write line 1 as the answer, then 3–5 evidence bullets (number + source).
5. Facts worth keeping go to the knowledge base via the kb tools (`add_source`, `add_fact`); unknowns go to `add_gap`.

## Output

Line 1: answer. Then ≤ 5 bullets `claim — [source](url) — grade`. Then `Next:` one action. Full notes in `outbox/<task>.md` if > 120 words.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- At least one A or B source behind line 1.

## Pitfalls (learned)

- Summarising everything found instead of answering the question.
- Re-researching what the knowledge base already holds.
