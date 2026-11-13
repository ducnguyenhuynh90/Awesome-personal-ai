---
name: help-article
description: Writes a help article or macro that resolves one question. Use when a help-center article, FAQ, support macro or canned reply must be written or fixed.
metadata:
  department: customer-support
  tags:
  - faq
  - help center
  - help article
  - macro
  - canned reply
  - knowledge base article
  - how to
  examples:
  - Write an FAQ on why withdrawals take 24 hours
  - Make a support macro for failed GCash deposits
  writes_to:
  - outbox/
---

# help-article

Writes a help article or macro that resolves one question.

## Steps

1. One question per article; title = the question as users ask it.
2. Answer in the first sentence; steps numbered; ≤ 150 words.
3. Check facts with the owner team (payments, compliance); flag anything unverified.
4. Save to outbox/ in the target language(s).

## Output

Title · Answer (1 sentence) · Steps · When to contact support. Saved to outbox/.

## Quality checks

- Answer in the first sentence.
- Facts verified or flagged.
- Under 150 words.

## Pitfalls (learned)

- Policy language users cannot act on.
