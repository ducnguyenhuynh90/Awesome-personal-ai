---
name: pitch-draft
description: Drafts a pitch/proposal tailored to one account. Use when you need a sales pitch, partnership proposal, one-pager or deck outline for a specific counterpart.
metadata:
  department: sales-bd
  tags:
  - pitch
  - proposal
  - deck
  - one-pager
  - partnership
  - sales email
  - offer
  examples:
  - Draft a partnership proposal for the payment aggregator
  - Outline a sales deck for the CRM aimed at agencies
  writes_to:
  - outbox/
---

# pitch-draft

Drafts a pitch/proposal tailored to one account.

## Steps

1. Start from account-research output (run it if missing).
2. Structure: their problem → our solution → proof → offer → next step.
3. Proof must be real (case, metric, customer quote) with source; no invented logos or numbers.
4. Save to outbox/; never send.

## Output

Outline or draft in outbox/. Reply: line 1 = the core offer, then the 5-part structure in bullets.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- No invented proof points.
- Pricing/terms only as given by the owner.

## Pitfalls (learned)

- Feature dumps instead of the counterpart's problem.
