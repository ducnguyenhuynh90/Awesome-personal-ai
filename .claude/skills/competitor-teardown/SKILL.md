---
name: competitor-teardown
description: 'Dated teardown of one competitor; writes to knowledge/competitors. Use when you must analyse a competitor: funnel, onboarding, pricing/promos, payments, VIP/loyalty, positioning.'
metadata:
  department: market-research
  tags:
  - competitor
  - teardown
  - rival
  - benchmark
  - pricing
  - promo
  - vip
  - onboarding
  - funnel
  - positioning
  examples:
  - Tear down XYZBet's onboarding and promos in PH
  - How does our CRM compare to HubSpot on pricing?
  writes_to:
  - knowledge/competitors/
---

# competitor-teardown

Dated teardown of one competitor; writes to knowledge/competitors.

## Steps

1. Read the competitor node if it exists; research only stale/missing sections.
2. Sections: positioning · funnel/onboarding steps · pricing & promos · payments · retention/VIP · weaknesses.
3. Date every observation; screenshots go to knowledge/competitors/assets/ with the date in the file name.
4. End with 'What we should copy / avoid' (≤ 3 each), tied to a goal.
5. Write facts and relations (competes_with, uses, operates_in) to the knowledge base.

## Output

Line 1: the one thing that matters. Then sections as bullets, each dated and sourced. Copy/avoid list. Full teardown in outbox/.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Every observation dated.
- Copy/avoid tied to a goal.

## Pitfalls (learned)

- Describing features without the so-what for us.
