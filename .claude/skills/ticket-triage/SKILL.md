---
name: ticket-triage
description: Categorises and prioritises tickets and surfaces themes and urgent issues. Use when support tickets, complaints or chats must be categorised, prioritised or summarised into themes.
metadata:
  department: customer-support
  tags:
  - tickets
  - support
  - complaints
  - triage
  - chat logs
  - customer service
  - escalation
  examples:
  - Triage today's 200 support tickets
  - What are the top complaint themes this week?
---

# ticket-triage

Categorises and prioritises tickets and surfaces themes and urgent issues.

## Steps

1. Aggregate only: no names, emails, phone numbers in the output.
2. Categorise (payments, KYC, bonus, bug, account, other) and set priority (P1 money/security, P2 blocks use, P3 other).
3. List P1 items with counts and a suggested owner.
4. Themes: top 5 with counts and one anonymised example.

## Output

Line 1: P1 count + the top issue. Table: category | count | P1 | trend vs last period. Owners for P1.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- No personal data in output.
- P1 items have an owner.

## Pitfalls (learned)

- Treating volume as severity — one payment-loss ticket outranks 50 how-to questions.
