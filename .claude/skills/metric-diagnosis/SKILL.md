---
name: metric-diagnosis
description: Explains a metric move by decomposing it (segment, funnel step, mix, tracking). Use when a metric moved unexpectedly and someone asks why (drop, spike, anomaly).
metadata:
  department: data
  tags:
  - why
  - drop
  - dropped
  - spike
  - anomaly
  - decline
  - increase
  - root cause
  - diagnose
  examples:
  - Why did FTD drop 15% in Mexico this week?
  - Conversion spiked yesterday — real or tracking?
---

# metric-diagnosis

Explains a metric move by decomposing it (segment, funnel step, mix, tracking).

## Steps

1. Confirm the move is real: tracking changes, releases, data delays.
2. Decompose: by market, platform, channel, new vs returning, funnel step.
3. Find where the change concentrates; check mix shift vs rate change.
4. Cross-check with events: releases, campaigns, payment outages, competitor promos (knowledge base).
5. Give the most likely cause with confidence and the next check.

## Output

Line 1: most likely cause + confidence. Then the decomposition table (segment | before | after | contribution). Next check.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Tracking issues ruled in or out first.

## Pitfalls (learned)

- Stopping at the first plausible story without checking mix shift.
