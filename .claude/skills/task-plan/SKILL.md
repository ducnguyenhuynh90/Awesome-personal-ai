---
name: task-plan
description: 'Plans a multi-step, multi-department task: sub-tasks, owner agent, dependencies, done-check. Use when a request spans several departments or steps and must be split into sub-tasks with owners and an order.'
metadata:
  department: staff
  tags:
  - plan
  - project
  - multi-step
  - cross-team
  - coordinate
  - break down
  - launch plan
  examples:
  - Plan the launch of our CRM in Mexico across product, marketing and compliance
  - Prepare everything for the board meeting next week
---

# task-plan

Plans a multi-step, multi-department task: sub-tasks, owner agent, dependencies, done-check.

## Steps

1. Write the definition of done in one line.
2. Split into ≤ 6 sub-tasks; each has one owner agent (from org/REGISTRY.md), exact input ids (files, nodes, links — no vague references), output file, a one-line done-check, and a one-line restatement by the owner before it starts.
3. Order by dependency; run independent sub-tasks in parallel.
4. Write work/<task>/tasks.json and work/<task>/progress.md so a restart can resume.
5. Merge results; send to reviewer; deliver one answer.

## Output

work/<task>/tasks.json: [{id, owner, input, output, depends_on, status}]. Reply: line 1 = the plan's outcome; then the sub-task list.

## Quality checks

- Each sub-task has exactly one owner.
- Done-check is observable.

## Pitfalls (learned)

- Splitting into many tiny tasks that each re-read the same context.
