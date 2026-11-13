---
name: budget-variance
description: Budget vs actual analysis with drivers. Internal use; aggregates only. Use when spend must be compared to budget or forecast, or a cost overrun explained.
metadata:
  department: finance
  tags:
  - budget
  - spend
  - variance
  - forecast
  - cost
  - overrun
  - burn
  - expenses
  examples:
  - Why is marketing spend 20% over budget this month?
  - Budget vs actual for Q3 by department
---

# budget-variance

Budget vs actual analysis with drivers. Internal use; aggregates only.

## Steps

1. Get budget and actuals from the system of record (read-only); state the as-of date.
2. Variance by line: absolute, %, and driver (price, volume, timing, one-off).
3. Flag the top 3 variances and whether they recur.
4. Mark the output INTERNAL; non-public financials never go into external drafts or the shared knowledge base.

## Output

Line 1: total variance + main driver. Table: line | budget | actual | var | driver. Marked INTERNAL.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Marked INTERNAL.
- As-of date stated.

## Pitfalls (learned)

- Confusing timing differences with real overruns.
