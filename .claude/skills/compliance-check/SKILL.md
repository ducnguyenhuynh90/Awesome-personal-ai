---
name: compliance-check
description: Flags regulatory risks with sources. Not legal advice; escalates to counsel. Use when a plan, feature, campaign or market entry must be checked against regulation, licensing, KYC/AML, ad or data-protection rules.
metadata:
  department: legal-compliance
  tags:
  - compliance
  - regulation
  - legal
  - kyc
  - aml
  - license
  - gdpr
  - data protection
  - allowed
  - ad rules
  - responsible gaming
  examples:
  - Is this bonus campaign allowed under PH advertising rules?
  - What KYC do we need to launch deposits in Thailand?
  - Does storing phone numbers in this way break data protection law?
  writes_to:
  - knowledge/regulators/
---

# compliance-check

Flags regulatory risks with sources. Not legal advice; escalates to counsel.

## Steps

1. Identify jurisdiction(s) and the activity.
2. Find the governing rule from A sources (regulator, statute); quote the clause and date.
3. Rate: clear / risk / blocker, with the specific clause.
4. Always end with: 'Not legal advice — confirm with counsel before launch' and name what to ask counsel.
5. Write confirmed rules to knowledge/regulators or markets.

## Output

Line 1: clear / risk / blocker + the rule. Clause quote + link + date. Questions for counsel.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Every rule from an A source, quoted and dated.
- Counsel escalation line present.

## Pitfalls (learned)

- Treating an article about a rule as the rule.
- Giving a definitive legal opinion.
