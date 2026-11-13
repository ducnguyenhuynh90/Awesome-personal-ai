---
name: draft-in-voice
description: Drafts text in the owner's voice from a style file. Never sends. Use when you must write a message, email, post or doc that will go out under a person's name.
metadata:
  department: shared
  tags:
  - draft
  - write
  - email
  - message
  - reply
  - announcement
  - post
  - slack
  examples:
  - Draft a reply to the vendor saying we need two more weeks
  - Write the Slack announcement for the new release
  writes_to:
  - outbox/
---

# draft-in-voice

Drafts text in the owner's voice from a style file. Never sends.

## Steps

1. Load the voice file named in the task (default `harness/style/<owner>_voice.md`; if missing, use plain, short, direct).
2. Write line 1 as the point of the message. Keep it to what the reader must know or do.
3. Save the draft to `outbox/<task>-draft.md` with the recipient and channel at the top.
4. Reply with the draft and: 'Reply go to send' — never send yourself.

## Output

```
To: <who> · Channel: <email/slack/...>
<draft>
```
Then one line: what you assumed.

## Quality checks

- Point of the message in the first sentence.
- No promises, numbers or dates the requester did not give.
- Nothing sent; draft saved in outbox/.

## Pitfalls (learned)

- Adding pleasantries and filler the owner never writes.
- Inventing commitments to make the draft sound complete.
