# Decisions (append-only, ADR style)

Format: date · decision · why · alternatives rejected · who. Do not re-open a settled decision without new evidence.

## D-001 · 2026-11-13 · Robin is an agent org, not a single agent
- Decision: one `chief-of-staff` front door, one department agent per function (12), shared skill library, one reviewer.
- Why: David wants any team's task handled (product, marketing, research, CEO, ...). Department agents keep each prompt short and owned.
- Rejected: one generalist agent with 40 skills (routing and context bloat); hundreds of persona agents (overlap breaks routing).
- Who: David (request), Claude (design).

## D-002 · 2026-11-13 · `.claude/agents` and `.claude/skills` are the source of truth
- Decision: agents and skills are Claude Code subagent / agentskills.io files. Robin-only fields go under `metadata:`.
- Why: the same files work in interactive Claude Code, the Agent SDK daemon, and the router. No framework lock-in
  (AutoGen is in maintenance mode, langgraph-supervisor is archived — see docs/research/agent-teams.md).
- Rejected: CrewAI/MetaGPT YAML, a custom agent DSL.
- Who: Claude.

## D-003 · 2026-11-13 · Deterministic BM25 router + model choice (two-level routing)
- Decision: `robin route` ranks agents (own text + owned skills) and skills offline; the shortlist goes into the
  chief-of-staff prompt; the department agent picks the final skill.
- Why: spec v2 dropped the classifier router, but with 12 departments and 38 skills the model should not see the
  whole catalogue every call. BM25 is free, explainable, testable (`robin eval routing`).
- Rejected: embeddings (need a provider → data leaves the VM, extra SOP approval); LLM classifier call per request.
- Who: Claude.

## D-004 · 2026-11-13 · Fact format = spec §15.3, not §5
- Decision: `- [date] fact — [[src-id]] — A|B|C (flags)`. Expiry is node-level (`expires:` in frontmatter).
- Why: §5 and §15 conflicted; source ids give traceable, deduplicated sources.
- Who: Claude (review), pending David's confirmation.

## D-005 · 2026-11-13 · Superseded facts are marked, never moved or deleted
- Decision: wrong/old facts get `(superseded by <date>)`; whole nodes move to `_archive/` only when retired.
- Why: §5 (move to `_archive/`) and §15.6 (never delete) conflicted; `kb stale` and the brief need to see history.
- Who: Claude, pending David.

## D-006 · 2026-11-13 · Edge vocabulary amended
- Decision: `causes` folded into `impacts` (note `causal`); `decided_by` dropped (no person nodes); added `targets`, `part_of`.
  `goal` and `decision` are not node types — goals live in `harness/goals.md`, decisions here.
- Why: avoid overlapping edges and notes about people.
- Who: Claude, pending David.

## D-007 · 2026-11-13 · Generated files are committed
- Decision: `knowledge/*/_index.md`, `knowledge/graph.json`, `org/REGISTRY.md` are generated and committed; the
  pre-commit hook regenerates and lints.
- Why: a cold agent can read them without running anything.
- Who: Claude.

## D-008 · 2026-11-13 · `kb lint` is check-only
- Decision: lint never edits; `kb index` flips expired → stale.
- Why: a commit hook must not change files under the author.
- Who: Claude.

## D-009 · 2026-11-13 · Single writer for knowledge
- Decision: all knowledge writes go through `robin.kb.writer` (file lock, secret redaction, username stripping,
  changelog), exposed to agents as in-process MCP tools `mcp__kb__*`. Agents have no shell.
- Why: modes A/B/C run concurrently; free-form file edits would race and bypass redaction.
- Who: Claude.

## D-010 · 2026-11-13 · Restricted departments
- Decision: finance, people and legal-compliance agents are `sensitivity: restricted`: outputs go only to the
  requester, nothing goes to the shared knowledge base, and people-partner never touches HR records.
- Why: S5 never-expose rules (HR/legal records, payout formulas, non-public financials, confidential contracts).
- Who: Claude.
