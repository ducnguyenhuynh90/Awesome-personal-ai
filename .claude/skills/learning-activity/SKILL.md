---
name: learning-activity
description: Designs or reviews an online workshop, quiz or learning game against 8 musts (goal, real cases, explain why, use the skill, meaningful score, self-play, 3-learner test, plain words). Use when a training, e-learning module, quiz, assessment or certification activity must be built or checked.
metadata:
  department: people
  tags:
  - e-learning
  - training
  - workshop
  - quiz
  - learning game
  - assessment
  - certification
  - course
  examples:
  - Build a 20-minute quiz that certifies CS agents on VIP handling
  - Review this training game before we launch it to the team
  writes_to:
  - outbox/
---

# learning-activity

Designs or reviews a workshop, quiz or learning game that teaches and certifies a real skill.

## Steps

1. **Start with the goal.** Write what people should do better at work after this, and how you will know it worked.
   A quick check by their lead is enough. No made-up numbers.
   Test the goal: it shows behaviour changing on the job (a lead sees it in real work), not completion ("all finish by
   Friday"), self-rating ("confidence 8/10") or a business result many things move ("sales +10%").
2. **Use real work cases.** Take them from the real job. Remove real names, IDs and amounts first.
3. **Always explain why.** Every answer, right or wrong, shows the reason.
4. **Make them use the skill.** Learners answer from memory. Guessing must not win: wrong options are real mistakes
   people make, and the right one does not stand out (similar length, no "all of the above", no odd one out).
5. **Make the score mean something.** A good score = they can really do it. End with a few new cases, so they show the
   skill, not memory of earlier items. If you use a pass mark, set it before launch.
6. **Play it yourself first.** Try every path and every wrong answer. Per question: is it clear? Could 2 answers be
   right? Is any wrong answer silly?
7. **Then test with 3 learners.** Fix what confuses them. To get ideas, challenge the AI openly. To fix a problem, say
   exactly what you saw and what should happen.
8. **Use plain words.** In the learners' language. 1 word per thing (do not switch between synonyms).

## Output

Goal + how it is checked · item list (case, options, right answer, why for each option) · final new-case set · pass mark
(if any) · self-play and 3-learner notes. Saved to outbox/. Reply = line 1 the verdict or the build, ≤ 120 words.

## Quality checks

- Goal names a work behaviour and who checks it; no invented numbers.
- No real names, IDs or amounts in cases.
- Every option has a "why".
- No item where 2 answers could be right or a wrong option is silly.
- Last items are new cases; pass mark fixed before launch.

## Pitfalls (learned)

- Goals that measure completion, self-rated confidence or a broad business metric instead of behaviour at work.
- The right answer is the longest or most detailed option.
