---
name: interview-plan
description: Designs a structured interview loop mapped to the scorecard. Use when a structured interview loop, questions or a take-home exercise must be designed for a role.
metadata:
  department: people
  tags:
  - interview
  - questions
  - hiring loop
  - take-home
  - assessment
  - candidate evaluation
  examples:
  - Design the interview loop for a product manager
  - Give me 8 questions to test SQL and product sense
  writes_to:
  - outbox/
---

# interview-plan

Designs a structured interview loop mapped to the scorecard.

## Steps

1. Map each scorecard competency to one interview stage.
2. Behavioural and work-sample questions with what good / bad answers look like.
3. Scoring rubric 1–4 per competency.
4. Evaluations of specific candidates are out of scope (HR records); this skill designs the process only.

## Output

Stages table (stage | competency | format | interviewer role). Questions with rubric. Saved to outbox/.

## Quality checks

- Every competency is assessed once.
- Rubric defines good and bad answers.

## Pitfalls (learned)

- Brain-teasers that predict nothing.
