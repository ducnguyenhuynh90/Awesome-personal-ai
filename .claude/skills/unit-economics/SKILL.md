---
name: unit-economics
description: Computes unit economics with every input sourced and the formula shown. Use when you need CAC, LTV, payback, margin or the economics of a product, channel or market.
metadata:
  department: finance
  tags:
  - cac
  - ltv
  - payback
  - margin
  - unit economics
  - roi
  - profitability
  - arpu
  examples:
  - What's our CAC payback for paid social in PH?
  - Is the CRM profitable per customer?
---

# unit-economics

Computes unit economics with every input sourced and the formula shown.

## Steps

1. Define each input (CAC, ARPU, gross margin, churn) and its source/query.
2. Show the formula and the result; sensitivity for the two most uncertain inputs.
3. Never expose payout formulas or non-public financials outside the requester.
4. Verdict vs target payback/LTV:CAC.

## Output

Line 1: verdict + the key ratio. Inputs table (value, source). Formula. Sensitivity.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Formula shown.
- Inputs sourced.

## Pitfalls (learned)

- Using blended CAC to judge a single channel.
