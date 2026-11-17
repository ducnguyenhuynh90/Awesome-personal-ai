---
name: idea-to-hypothesis
description: Turns an idea into problem → evidence → hypothesis → experiment, with a framing gate. Use when an idea, complaint or opportunity must become a testable hypothesis or experiment.
metadata:
  department: product
  tags:
  - idea
  - hypothesis
  - experiment
  - test
  - a/b
  - opportunity
  - problem
  examples:
  - Turn 'add GCash cashback' into a testable hypothesis
  - We think onboarding is too long — how do we test that?
---

# idea-to-hypothesis

Turns an idea into problem → evidence → hypothesis → experiment, with a framing gate.

## Steps

1. Problem: who has it, how often, evidence (data or VoC). No evidence → stop and list what data is needed.
2. Hypothesis: 'If we <change> for <segment>, <metric> moves from X to Y because <reason>.'
3. Experiment: variant, control, audience, sample size / duration estimate, primary metric, guardrail metrics.
4. Decision rule written before launch: ship / iterate / kill thresholds.
5. Check market rules (e.g. TH phone-login only) and KPI impact (D2 deposit retention, LTV).

## Output

Problem · Evidence · Hypothesis · Experiment (variant, audience, metric, guardrails, duration) · Decision rule · Risks.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Decision rule exists before launch.
- Guardrail metric named.

## Pitfalls (learned)

- Hypotheses with no metric or no baseline.
- Running a test too small to detect the expected change.
- Long chat replies: put the full design in outbox/ and reply with the hypothesis line, the primary metric and the questions for David (learned 2026-11-13 smoke test).
