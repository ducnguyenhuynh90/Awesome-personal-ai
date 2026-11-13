---
name: prioritize-backlog
description: Ranks a backlog with an explicit scoring model (RICE or impact/effort). Use when a list of features, bugs or ideas must be ranked or a roadmap trade-off made.
metadata:
  department: product
  tags:
  - prioritize
  - roadmap
  - backlog
  - rank
  - rice
  - what first
  - trade-off
  examples:
  - Rank these 12 backlog items for next sprint
  - What should the product team build first this quarter?
  context:
  - harness/goals.md
---

# prioritize-backlog

Ranks a backlog with an explicit scoring model (RICE or impact/effort).

## Steps

1. Get the list and the goal it serves (harness/goals.md).
2. Score each: reach, impact on the goal metric, confidence (evidence grade), effort — state the source of every estimate.
3. Rank; show the top 5 and the cut line.
4. Flag dependencies and anything blocked by compliance.

## Output

Table: item | reach | impact | confidence | effort | score. Then the cut line and 2 lines of rationale.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Confidence reflects evidence, not enthusiasm.

## Pitfalls (learned)

- Precise scores built on guesses — show the confidence column honestly.
