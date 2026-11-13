---
name: okr-review
description: Reviews goals against current metrics and recommends where to focus. Use when goals, OKRs or KPIs must be checked for progress, gaps or next-quarter planning.
metadata:
  department: executive
  tags:
  - okr
  - goal
  - quarter
  - kpi
  - progress
  - planning
  - priorities
  - targets
  examples:
  - How are we tracking against Q4 goals?
  - Draft next quarter's OKRs for the product team
  context:
  - harness/goals.md
---

# okr-review

Reviews goals against current metrics and recommends where to focus.

## Steps

1. Read `harness/goals.md` (or the goals file the task names).
2. For each goal, get the current metric value (delegate to data-analyst) and the target.
3. Mark on-track / at-risk / off-track with the number, not adjectives.
4. For at-risk goals: top cause (with evidence) and one action.
5. For planning: propose ≤ 3 objectives, each with one metric, a target and a 'what would change my mind' line.

## Output

Table: goal | metric | now | target | status | action. Then ≤ 3 lines of focus.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Every status has a number behind it.

## Pitfalls (learned)

- Counting activity (tasks shipped) as progress on an outcome metric.
