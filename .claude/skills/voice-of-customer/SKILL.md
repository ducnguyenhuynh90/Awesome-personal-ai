---
name: voice-of-customer
description: Mines reviews/social/tickets into pains ranked by frequency × severity. Use when you need what customers or players actually complain about or want, from reviews, social, forums or tickets.
metadata:
  department: market-research
  tags:
  - reviews
  - customer
  - player
  - voice
  - complaints
  - feedback
  - sentiment
  - pain points
  - app store
  examples:
  - What do players complain about in our PH app store reviews?
  - Top pains of small businesses using CRMs
  writes_to:
  - knowledge/players/
---

# voice-of-customer

Mines reviews/social/tickets into pains ranked by frequency × severity.

## Steps

1. Pick sources: app store reviews, Reddit/FB groups, support tickets (aggregate only).
2. Sample at least 50 items if available; note the sample size and date range.
3. Cluster into pains; score frequency (count) × severity (1–3: annoyance / blocks use / loses money).
4. Quote 1 anonymised example per pain (no usernames).
5. Write the top pains to knowledge/players/ as nodes linked with impacts → metric.

## Output

Line 1: the #1 pain and its share. Table: pain | freq | severity | score | example. Sample: n, sources, dates.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Sample size stated.
- No usernames or personal data.

## Pitfalls (learned)

- Over-weighting a few loud reviews.
- Mixing feature requests with pains.
