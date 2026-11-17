# Proposal: a stronger safety gate (David approves — `guard/` and `evals/` are his)

Status: APPROVED by David 2026-11-13 ("go all") and applied: guard/approval_gate.py, config/action_rules.yaml,
`send:` per connector in config/integrations.yaml, taint marking in robin/orchestrator.py, `robin approve`,
evals/memory (baseline precision 0.88, recall 1.00).

Sources: Meta Muse (Sentinel), OpenAI dots (action rules), xAI Grok Bot and its open clone (approval memory).
See docs/research/agent-teams.md for what is verified vs not.

1. **Taint (Meta Muse, verified).** Once a task has read untrusted content (web, email, Slack, files), every write
   in that task needs a per-draft token — no standing approval applies. Muse relies on this because prompt
   injection is still unsolved. Fit: `guard/untrusted.wrap()` marks the task tainted in the trace;
   `approval_gate.decide()` ignores `always` grants for tainted tasks. Effort S.
2. **Four action behaviours (OpenAI dots, verified).** `config/action_rules.yaml`: `{pattern, behaviour: auto |
   when_told | ask | handoff}`. A hard-coded **always-handoff** list nobody can override: pay / transfer / refund /
   payout / credentials / password / permission / deploy / delete / publish. `decide()` reads rules before tokens.
   Effort M.
3. **Scoped, expiring grants (Muse, unverified; Grok clone).** Token scopes `once | task | until:<date>`; the call
   must match the granted tool and target exactly; `once` is consumed on use. Effort M.
4. **Circuit breaker (Codex docs; Grok clone).** 3 denials in a row in one task → stop the task and report. A denied
   call is never retried; a new message from David expires pending approvals. Effort S.
5. **Read vs send per connector.** `send: off` per tool in `config/integrations.yaml` makes a connector read-only
   even with a token. Effort S.
6. **Memory retrieval eval (New Computer's Dot).** `evals/memory/cases.yaml`: labelled queries → expected profile /
   knowledge lines from synthetic owners; score precision and recall of `kb query` + profile retrieval. Effort M.

Already built without touching guard/: proactive routines run with no external tools and no shell/edit tools,
so they are read-only by construction (robin/orchestrator.py, `proactive=True`).
