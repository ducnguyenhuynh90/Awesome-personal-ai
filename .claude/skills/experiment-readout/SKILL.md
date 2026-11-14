---
name: experiment-readout
description: Reads out an experiment against its pre-registered decision rule. Use when an A/B test or experiment has data and needs a result and a ship/kill call.
metadata:
  department: data
  tags:
  - experiment
  - a/b
  - test result
  - readout
  - significance
  - variant
  - uplift
  - did
  - impact
  - lift
  - worked
  - effect
  - campaign result
  - increase
  examples:
  - Read out the GCash cashback test
  - Did the new onboarding variant win?
---

# experiment-readout

Reads out an experiment against its pre-registered decision rule.

## Steps

1. Find the pre-registered hypothesis and decision rule (idea-to-hypothesis output).
2. Check sample ratio mismatch and duration; stop if broken.
3. Primary metric: effect, confidence interval, p-value or posterior; guardrails.
4. Apply the decision rule: ship / iterate / kill. No rule → say so.

## Output

Line 1: ship/iterate/kill + effect with CI. Then guardrails, SRM check, caveats.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- SRM checked.
- Decision follows the pre-registered rule.

## Pitfalls (learned)

- Peeking and calling a winner early.
- Ignoring a guardrail regression.
