---
name: source-grading
description: Grades a source A/B/C and decides whether a claim may be used. Use when you must decide how far to trust a source, or a research skill tells you to grade sources.
metadata:
  department: shared
  tags:
  - source
  - grade
  - trust
  - verify
  - citation
  - evidence
  examples:
  - Is this blog post a reliable source for the PH license count?
  - Grade these five links before I use them
---

# source-grading

Grades a source A/B/C and decides whether a claim may be used.

## Steps

1. Identify who published it and whether they are the primary owner of the fact (regulator, company, dataset owner).
2. Grade: A = official/primary (regulator, company filing, our own data); B = reputable secondary (major press, analyst firm, app store listing); C = unverified (forums, blogs, social, AI summaries).
3. Check the date. Anything older than 12 months about prices, rules or promos is at most B and gets a short expiry.
4. C claims are dropped unless the task is about sentiment (reviews, forums) — then they are kept and labelled as opinion.
5. Two independent B sources agreeing can support a decision; one C never can.

## Output

`src-id | grade | publisher | date | why` — one line per source.

## Quality checks

- Every source has a grade and a date.
- No C source supports a number in line 1.

## Pitfalls (learned)

- Treating a news article that quotes a regulator as A — the regulator page is A, the article is B.
- Using an AI-generated summary page as a source.
