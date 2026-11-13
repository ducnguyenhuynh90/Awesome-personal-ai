# HANDOVER (rewrite at the end of every session)

Last session: 2026-11-13, Claude Code (cloud), branch `claude/robin-v2-agent-spec-t6sx7r`.

## State in 5 lines
1. Agent org built: chief-of-staff + 12 department agents + reviewer (`.claude/agents/`), 38 skills (`.claude/skills/`).
2. Offline router works: routing eval 52/54 agent (96%), 54/54 skill-in-top-3; holdout 17/18 (94%) / 18/18.
3. Knowledge layer (spec §15) works: schema, lint, index, query, stale, locked writer, `mcp__kb__*` tools; 5 seed market nodes, no facts.
4. Guards work and are tested: approval gate (default deny), untrusted wrapper, secret scanner. 27 tests pass.
5. Orchestrator (`robin ask`) is written against claude-agent-sdk 0.2.172 but has NOT run live: no Anthropic credentials in the build container.

## In progress → next concrete step
- Live P0 acceptance: on the VM with credentials, run `robin ask "<PH KYC question>"`, then `robin eval process`; record cost here.
- Seed PH knowledge: David gives 5 sourced facts → `robin kb add-source` + `add-fact` for each.
- Slack DM listener + daemon/scheduler (spec §4 B/C) — not started.

## Blockers
- AI Tool Request SOP (Notion) must be filed before company connectors (Slack, Gmail, Notion, PostHog) are wired.
- Anthropic credentials and Slack app tokens on the VM.

## Open questions for David
1. Confirm DECISIONS D-004 → D-006 (fact format, supersede-not-delete, edge vocabulary).
2. Which departments matter first beyond product/research/data? (All 12 exist; tune the top 3 with real asks.)
3. Fill `harness/goals.md` with Q4 goals — mode C (autonomous agenda) depends on it.

## Do NOT redo
- Framework research (docs/research/agent-teams.md) — settled: files + Agent SDK, no CrewAI/AutoGen.
- Router choice — BM25 + two-level routing, measured; improve descriptions/examples, not the algorithm.
- Agents/skills were bootstrapped by a one-off generator; edit the files directly now (they are the source of truth).
