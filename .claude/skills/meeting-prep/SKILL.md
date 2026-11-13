---
name: meeting-prep
description: 'Builds a one-page meeting brief from calendar, messages and knowledge. Use when someone has a meeting coming up and needs a one-page prep: goal, context, asks, risks.'
metadata:
  department: shared
  tags:
  - meeting
  - prep
  - agenda
  - call
  - '1:1'
  - brief me
  examples:
  - Prep me for tomorrow's call with the payment partner
  - What do I need to know before the board meeting?
---

# meeting-prep

Builds a one-page meeting brief from calendar, messages and knowledge.

## Steps

1. Find the meeting (calendar, if connected) and the attendees' last 3 relevant threads.
2. Pull related knowledge nodes with the kb `query` tool.
3. Write: goal of the meeting, what we want from them, what they likely want, open issues, 3 questions to ask.
4. Flag any decision that needs data you do not have.

## Output

Goal · Our ask · Their likely ask · Open issues (≤3) · Questions (3) · Risks (≤2). ≤ 200 words.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Every open issue cites a message or doc.

## Pitfalls (learned)

- Biography-style attendee summaries nobody asked for.
