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
- Who: Claude (review). Confirmed by David 2026-11-13.

## D-005 · 2026-11-13 · Superseded facts are marked, never moved or deleted
- Decision: wrong/old facts get `(superseded by <date>)`; whole nodes move to `_archive/` only when retired.
- Why: §5 (move to `_archive/`) and §15.6 (never delete) conflicted; `kb stale` and the brief need to see history.
- Who: Claude. Confirmed by David 2026-11-13.

## D-006 · 2026-11-13 · Edge vocabulary amended
- Decision: `causes` folded into `impacts` (note `causal`); `decided_by` dropped (no person nodes); added `targets`, `part_of`.
  `goal` and `decision` are not node types — goals live in `harness/goals.md`, decisions here.
- Why: avoid overlapping edges and notes about people.
- Who: Claude. Confirmed by David 2026-11-13.

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
- Why: company never-expose rules (HR/legal records, payout formulas, non-public financials, confidential contracts).
- Who: Claude.

## D-011 · 2026-11-13 · Start with four departments
- Decision: product, market research, data and marketing are active first (`config/org.yaml`). The other eight
  agents stay in the repo but the router does not send work to them; asks for them go to the chief of staff,
  which says the department is not active yet and handles what it can with research-brief.
- Why: tune a few departments on real asks before widening; routing among 4 is easier to get right.
- Rejected: deleting the other agents (they cost nothing while inactive and keep the catalogue complete).
- Who: David.

## D-012 · 2026-11-13 · Patterns from Meta Muse and xAI Grok Bot
- Decision: adopt agent contracts (owns / not_owns / source_of_truth / needs_approval / autonomy, validated, one
  owner per capability), verify-before-done (proof attached, stop after 2 failed attempts), a `SILENT` outcome,
  a readable owner profile with remember/forget (gitignored), and a learning loop that turns one correction into
  one general rule per week behind an overfit check. Approval scopes are proposed, not applied (guard/ is David's).
- Why: both products keep each agent to one job, learn principles not stories, and stay quiet by default —
  the same direction as spec §2, with concrete mechanisms we lacked.
- Rejected for now: always-on per-agent computers, multi-agent "staff meeting" for every task (cost), autopilot
  autonomy (no agent has earned it yet).
- Who: David (asked), Claude.

## D-013 · 2026-11-13 · Routines, check-ins and handoffs from Muse / Grok Bot / dots
- Decision: routines are typed contracts (config/routines.yaml, validated) that run in a read-only proactive mode
  (no external tools, no shell/edit), reply SILENT unless `notify_if` is met, report FAILED instead of using old data,
  and are logged with run limits and a silent-streak slowdown. Check-ins build their digest in code (zero tokens when
  silent). Handoffs carry exact ids and a done-line. Profile lines carry source and status; forget by source.
- Why: all three products converge on quiet-by-default, read-only background work and typed schedules; these fit
  spec §2.6–2.8 and cut cost.
- Gate changes (taint, action rules, scoped grants, breaker) and a memory eval are proposed for David, not applied.
- Who: David (asked), Claude.

## D-014 · 2026-11-13 · Gate v2 and memory eval
- Decision: the approval gate checks, in order: hard hand-off (money, credentials, permissions, deploy, delete,
  publish — never an agent), read-only connectors (`send: false`), a circuit breaker (3 denials in a row), reads and
  drafts, action rules (auto | when_told | ask | handoff; default ask), then grants (once | task | until:DATE, exact
  input match). A task that read untrusted content (web, connectors, raw sources) loses auto rules and standing
  grants. Denials say "do not retry"; `ask` leaves a pending file the check-in shows. Memory retrieval is measured
  by evals/memory (synthetic fixture; baseline P 0.88, R 1.00).
- Why: Meta Muse (Sentinel, taint), OpenAI dots (action behaviours, always-human list), Grok Bot (approval memory).
- Who: David ("go all").

## D-015 · 2026-11-14 · Run on Claude Code cloud
- Decision: (1) a SessionStart hook installs Robin in cloud sessions; (2) the approval gate also runs as a Claude
  Code PreToolUse/PostToolUse hook, scoped to company connector tools (session id = task id; reads and repo work
  untouched; infrastructure and GitHub tools exempt); (3) a cloud scheduled task runs the daily knowledge scan in a
  fresh session (web only, no connectors), pushing knowledge to `robin/knowledge-updates`.
- Why: David wants Robin on cloud Claude; Claude itself is the model there, so no API key or VM is needed for
  interactive use or the daily routine.
- Who: David ("all three").
