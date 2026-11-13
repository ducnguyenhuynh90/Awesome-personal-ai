---
name: content-calendar
description: 'Builds a content calendar tied to a goal and audience. Use when someone needs a content or social media plan over weeks: topics, formats, channels, cadence.'
metadata:
  department: marketing
  tags:
  - content
  - calendar
  - social
  - seo
  - blog
  - posts
  - tiktok
  - facebook
  - editorial
  examples:
  - Make a 4-week social content plan for our Bangladesh launch
  - Plan SEO blog topics for the CRM product
  writes_to:
  - outbox/
---

# content-calendar

Builds a content calendar tied to a goal and audience.

## Steps

1. Goal and audience; pull audience pains from knowledge/players.
2. 3–4 content pillars tied to the goal.
3. Calendar rows: date, channel, format, topic, hook, CTA, owner.
4. Note platform and market rules (e.g. gambling ad restrictions).

## Output

Pillars (≤4) then a table: date | channel | format | topic | hook | CTA. Saved to outbox/ as CSV or md.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Every post maps to a pillar and the goal.

## Pitfalls (learned)

- Calendars with no hook or CTA — just topics.
