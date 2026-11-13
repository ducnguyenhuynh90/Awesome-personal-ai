# Proposal: approval scopes in the safety gate (David approves — `guard/` is his)

Status: **awaiting David** ("go gate"). Not applied: edits to `guard/` were blocked as loosening oversight.

From Meta Muse (Sentinel) and Grok Bot (approval memory):

1. **Allow once** (default): `approvals/<task>.json` with `"scope": "once"` is consumed on first use.
   Today a task token can be reused for the whole task.
2. **Always allow** for safe, repetitive writes (e.g. posting a draft to David's own DM):
   `approvals/always.json`, set only by `robin approve --always`. Hard-refused for any tool matching
   pay / payment / transfer / refund / payout / deploy / release / permission / role / grant / delete / remove / drop.
3. **Read vs send per connector**: keep reads automatic (`get/list/search/read/fetch/query`), send always gated —
   already true; add a per-connector `send: off` switch in `config/integrations.yaml` so a connector can be read-only
   even with a token.
4. **Don't allow = don't retry**: on deny, the hook reason tells the agent not to retry the same call.

Risk: "always" widens what runs without a per-task "go". Mitigation: the never-always list, and `robin doctor`
lists every standing approval.
