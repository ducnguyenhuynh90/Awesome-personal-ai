# HANDOVER (rewrite at the end of every session)

Last session: 2026-11-13, Claude Code (cloud), branch `claude/robin-v2-agent-spec-t6sx7r`.

## State in 5 lines
1. Agent org built: chief-of-staff + 12 department agents + reviewer (`.claude/agents/`), 38 skills (`.claude/skills/`).
2. Offline router works: routing eval 52/54 agent (96%), 54/54 skill-in-top-3; holdout 17/18 (94%) / 18/18.
3. Knowledge layer (spec §15) works: schema, lint, index, query, stale, locked writer, `mcp__kb__*` tools; 5 seed market nodes, no facts.
4. Guards work and are tested: approval gate (default deny), untrusted wrapper, secret scanner. 27 tests pass.
5. Orchestrator (`robin ask`) is written against claude-agent-sdk 0.2.172 but has NOT run live: no Anthropic credentials in the build container.

## Since then (2026-11-13, second pass)
- David confirmed D-004 to D-006. Active departments = product, market research, data, marketing (D-011, config/org.yaml).
- Router ranks all departments, then filters; asks for inactive departments go to chief-of-staff flagged `inactive`. 30 tests pass.
- Live smoke test of the 4 agents: safe and honest, but all broke the 120-word cap; research cited unopened pages.
  Fixes are proposed, not applied (`.claude/` and `evals/` are David's): docs/proposals/2026-11-13-first-four-departments.md.

- David approved ("fix all"): proposal items 1–8 applied. Routing: focus 10/10, cases 53/54, holdout 17/18 (holdout never tuned).
- Re-test after fixes: data-analyst now ~125 words with ONE definition question (was ~250); research opens sources and stops
  when it can't (was citing snippets); marketing marks conditional variants. But research (~200), product (~280) and marketing
  (~250) still exceeded 120 words → the cap is now enforced in code: `robin/orchestrator.py:enforce_cap` saves the full answer
  to outbox/<task>-full.md, shortens once with the cheap model, and falls back to a deterministic trim. 33 tests pass.
- Network policy of the cloud session blocked gmanetwork.com and philstar.com; research needs bsp.gov.ph, pagcor.ph, inquirer.net.

- Company frameworks (third pass): read company-context + team-context skills. The repo is PUBLIC, so only methods
  were added to 13 agents (#BeClear, #Context, #DontPassMessage, escalate with a recommendation, labelled assumptions,
  Product's improvement loop / experiment gate / review depth, revenue-quality check). Company facts are read at
  runtime from those skills (or gitignored harness/private/ on the VM). Reviewer changes: docs/proposals/2026-11-13-reviewer-company-checks.md.
- Reply cap is now per skill: default 120 (config/limits.yaml reply_word_cap), research skills 250 (spec: one screen).

## In progress → next concrete step
- David decides: make the GitHub repo private? (spec, product names, markets, PostHog project id, his name are public now.)
- Live run on the VM: `robin eval process --only p12-brevity-research,p13-brevity-product,p14-brevity-data,p15-brevity-marketing`
  to confirm the code-enforced cap with the real orchestrator (subagent tests here bypass the orchestrator).
- Live P0 acceptance: on the VM with credentials, run `robin ask "<PH KYC question>"`, then `robin eval process`; record cost here.
- Seed PH knowledge: David gives 5 sourced facts → `robin kb add-source` + `add-fact` for each.
- Slack DM listener + daemon/scheduler (spec §4 B/C) — not started.

## Blockers
- AI Tool Request SOP (Notion) must be filed before company connectors (Slack, Gmail, Notion, PostHog) are wired.
- Anthropic credentials and Slack app tokens on the VM.

## Open questions for David
1. Metric definitions (FTD, D2 deposit retention, LTV, CAC payback) — data-analyst is blocked without them.
2. Approve docs/proposals/2026-11-13-first-four-departments.md.
3. Fill `harness/goals.md` with Q4 goals — mode C (autonomous agenda) depends on it.

## Do NOT redo
- Framework research (docs/research/agent-teams.md) — settled: files + Agent SDK, no CrewAI/AutoGen.
- Router choice — BM25 + two-level routing, measured; improve descriptions/examples, not the algorithm.
- Agents/skills were bootstrapped by a one-off generator; edit the files directly now (they are the source of truth).
