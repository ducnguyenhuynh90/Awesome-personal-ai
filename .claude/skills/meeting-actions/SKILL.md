---
name: meeting-actions
description: Extracts decisions, action items, owners and dates from notes or threads. Use when meeting notes, transcripts or long threads must become decisions, owners and deadlines.
metadata:
  department: operations
  tags:
  - meeting notes
  - action items
  - minutes
  - transcript
  - follow up
  - decisions
  - recap
  examples:
  - Turn this transcript into action items
  - Recap this 80-message Slack thread
---

# meeting-actions

Extracts decisions, action items, owners and dates from notes or threads.

## Steps

1. Decisions made (with who decided).
2. Action items: action, owner, due date (or 'no date — ask').
3. Open questions and who must answer.
4. Do not invent owners or dates.

## Output

Decisions · Actions table (action | owner | due) · Open questions. ≤ 150 words.

## Quality checks

- Every action has an owner or is flagged.
- No invented dates.

## Pitfalls (learned)

- Listing discussion points as decisions.
