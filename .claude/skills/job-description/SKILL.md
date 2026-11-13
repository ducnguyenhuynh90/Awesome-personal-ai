---
name: job-description
description: 'Writes a JD and scorecard from the role''s outcomes. Use when a role must be defined: job description, scorecard, or hiring brief.'
metadata:
  department: people
  tags:
  - job description
  - jd
  - role
  - hiring
  - recruit
  - position
  - scorecard
  - job post
  examples:
  - Write a JD for a senior data analyst
  - Create a scorecard for the growth marketer role
  writes_to:
  - outbox/
---

# job-description

Writes a JD and scorecard from the role's outcomes.

## Steps

1. Start from outcomes: what this person must achieve in 6 and 12 months.
2. Competencies that predict those outcomes; must-have vs nice-to-have.
3. Inclusive language; no age, gender or nationality requirements.
4. Save to outbox/.

## Output

Outcomes (6/12 mo) · Responsibilities · Must-have · Nice-to-have · Scorecard. Saved to outbox/.

## Quality checks

- Outcomes before requirements.
- No discriminatory criteria.

## Pitfalls (learned)

- Laundry lists of tools instead of outcomes.
