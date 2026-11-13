---
name: market-scan
description: 'Snapshot of one market: regulation, payments, main players, trends; writes to the knowledge base. Use when you need the current state of a market or country: regulation, payments, players, trends.'
metadata:
  department: market-research
  tags:
  - market
  - country
  - regulation
  - payments
  - landscape
  - trends
  - license
  - philippines
  - mexico
  - thailand
  - bangladesh
  - pakistan
  examples:
  - What are the current KYC rules for online deposits in the Philippines?
  - Give me a market scan of Mexico
  - Which payment methods dominate in Bangladesh?
  writes_to:
  - knowledge/markets/
  domains:
  - government regulator sites
  - central banks
  - app stores
  - major news
---

# market-scan

Snapshot of one market: regulation, payments, main players, trends; writes to the knowledge base.

## Steps

1. kb `query` tool with market=<mkt>, and read `knowledge/markets/market-<mkt>.md` summary first; only research what is missing or stale.
2. Sections: regulation (regulator, license, KYC, ad rules) · payments (methods, share, fees) · players (top 5) · trends.
3. Prefer A sources (regulator, central bank); grade with source-grading.
4. Answer the ask in ≤ 120 words; write new facts with the kb tools (`add_source`, then `add_fact`).
5. Record what you could not confirm with the kb `add_gap` tool.
6. Open every source you cite (WebFetch) and confirm the claim is on the page. Never cite from search-result snippets; unopened = not a source.

## Output

Line 1: the answer. Then ≤ 5 bullets `fact — source — grade`. `Next:` one action. Knowledge updated: list of node ids.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Regulation claims come from A sources or are flagged.
- New facts written to knowledge/markets/.

## Pitfalls (learned)

- Mixing up the national regulator and a local/provincial one.
- Using pre-2025 payment share data without flagging it.
- Citing search-result snippets without opening the page; grades were unverifiable (learned 2026-11-13 smoke test).
