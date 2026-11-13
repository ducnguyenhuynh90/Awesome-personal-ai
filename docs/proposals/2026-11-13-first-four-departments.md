# Proposal: lessons from the first live run of the four active departments

Status: **awaiting David's approval**. These changes touch `.claude/` and `evals/`, which CLAUDE.md reserves
for David, so they are proposed here instead of committed. Reply "go" to apply all, or name the items.

## Smoke test, 2026-11-13 (one real ask per department, run as Claude Code subagents)

| Agent | Ask | Line 1 answers | Sourced / no guessing | ≤ 120 words | Draft in outbox | Verdict |
|---|---|---|---|---|---|---|
| research-lead | PH deposit methods | yes ("can't give a sourced split; GCash/Maya most cited, all grade C") | yes — but cited **search snippets, never opened a page** | no (~330) | n/a | FAIL: brevity, evidence verified |
| product-lead | GCash 5% cashback → experiment | yes | yes — stopped at "no baseline", listed 7 data pulls | no (~300) | yes | FAIL: brevity |
| data-analyst | PH D2 deposit retention | yes ("not available; won't estimate") | yes — PostHog down, no definition in KB | no (~250) | n/a | FAIL: brevity |
| marketing-lead | 5 PH win-back pushes | yes | yes — flagged unconfirmed offer, limits, compliance | no (~280) | yes | FAIL: brevity |

What worked: no agent guessed a number, all drafts stayed in `outbox/`, every agent named its skill and its gaps,
marketing routed compliance to compliance-officer. What failed: **all four broke the 120-word cap** (detail belongs
in the outbox file), and **research cited unopened pages**.

Already done (allowed without approval): 3 gaps recorded in `knowledge/_gaps.md` (metric definitions, PH deposit
split, BSP e-wallet claim). The research agent's "facts to add" were **not** written: they came from search
snippets, so they are unverified.

## Proposed changes

### 1. All agents — `## How to work`, step 4 (replace)
> 4. Reply in the output contract: line 1 = answer or decision, then evidence (number + source). Count your words:
> the chat reply is ≤ 120 words, always. Tables, options, gaps and caveats go in an `outbox/` file that you link — not in the reply.

### 2. chief-of-staff — `## How to route`, new step 5
> 5. `inactive department` in the shortlist: tell David in one line that the department is not active yet
> (config/org.yaml) and offer what research-brief can do. Do not delegate to an inactive agent.

### 3. market-scan and research-brief — new last step + pitfall
> Step: Open every source you cite (WebFetch) and confirm the claim is on the page. Never cite from search-result
> snippets; unopened = not a source.
> Pitfall: Citing search-result snippets without opening the page; grades were unverifiable (2026-11-13).

### 4. metric-pull — new last step + pitfall
> Step: PostHog: region and project id from the company context (local config). If the metric has no definition in knowledge/metrics/,
> ask David ONE question proposing the most likely definition; do not list every variant.
> Pitfall: Answering "no access" with a long essay; the reply should be 3 lines: no number, why, the one thing needed.

### 5. copy-variants — pitfall
> Writing offer-dependent variants (bonus, expiry) without a confirmed offer — ask for offer, brand, payment
> method and character limits first, or mark those variants conditional.

### 6. idea-to-hypothesis — pitfall
> Long chat replies: put the full design in outbox/ and reply with the hypothesis line, the primary metric and the
> questions for David.

### 7. evals/routing/focus.yaml (new) — boundary cases between the four active departments
Run with the active-department config; inactive asks must go to chief-of-staff.

```yaml
cases:
  - {request: "What promos are competitors running in PH this month?", agent: research-lead, skill: competitor-teardown}
  - {request: "Design a promo to beat the competitor's welcome bonus", agent: marketing-lead, skill: campaign-brief}
  - {request: "Did the welcome bonus campaign increase FTD?", agent: data-analyst, skill: experiment-readout}
  - {request: "Should the welcome bonus become a permanent product feature? Write the spec", agent: product-lead, skill: prd-draft}
  - {request: "What do players say about our welcome bonus in reviews?", agent: research-lead, skill: voice-of-customer}
  - {request: "How many players claimed the welcome bonus last week?", agent: data-analyst, skill: metric-pull}
  - {request: "Write SMS copy announcing the new welcome bonus", agent: marketing-lead, skill: copy-variants}
  - {request: "Turn 'players abandon the cashier' into an experiment", agent: product-lead, skill: idea-to-hypothesis}
  - {request: "Write a job description for a CRM marketer", agent: chief-of-staff}
  - {request: "Summarise the obligations in our new payment provider contract", agent: chief-of-staff}
```

### 8. evals/process/cases.yaml — add a brevity case per active department
```yaml
  - {id: p12-brevity-research, request: "Which payment methods dominate online deposits in the Philippines?", checks: [under_cap, line1_answers]}
  - {id: p13-brevity-product, request: "Turn 'GCash 5% first-deposit cashback' into an experiment", checks: [under_cap, line1_answers]}
  - {id: p14-brevity-data, request: "What was D2 deposit retention in PH last week?", checks: [under_cap, says_dont_know]}
  - {id: p15-brevity-marketing, request: "Write 5 push variants to win back lapsed PH depositors", checks: [under_cap]}
```

## Needs David (blocks quality, not code)
1. Metric definitions (FTD, D2 deposit retention, LTV, CAC payback) or the Notion page that holds them.
2. PostHog connector: failed to connect in this session (502). Reconnect in Settings > Connectors.
3. For the drafts in `outbox/`: cashback form/cap, minimum worthwhile lift, PH registrants/week; push offer,
   brand, payment method and character limits.
