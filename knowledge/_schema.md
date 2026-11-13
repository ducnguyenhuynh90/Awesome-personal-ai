# Node schema (spec §15.3, amended — see DECISIONS.md)

File name = id (`knowledge/markets/market-ph.md` has `id: market-ph`). Ids are never renamed; add `aliases:` instead.

```yaml
---
id: competitor-xyzbet        # lowercase slug = file name
type: competitor             # one of knowledge/_types.yaml
status: active               # active | stale | archived | conflict
updated: 2026-11-13
confidence: B                # A official/primary · B reputable secondary · C unverified
expires: 2027-02-13          # node-level; `robin kb index` flips expired nodes to stale
markets: [ph, mx]
related: []                  # generated from ## Relations by tooling; do not hand-edit
sources: [src-0142]          # kept in sync by the kb tools
owner: robin                 # robin | david | <agent name>
summary: One sentence (≤ 30 words). What a reader needs if they read nothing else.
---
```

Body headers, exactly in this order:

```
## Facts
- [2026-11-13] fact — [[src-0142]] — A
- [2026-11-13] inferred thing — [[src-0142]], [[src-0157]] — B (inferred)
- [2026-10-01] old fact — [[src-0099]] — B (superseded by 2026-11-13)
## Relations
- operates_in [[market-ph]]
- impacts [[metric-ftd]] (-, causal, inferred)
## Open questions
- Do they run a D2 deposit bonus in MX? next try: app-store listing
## Changelog
- 2026-11-13 added promo structure (research-lead, task t-0931)
```

Edges (closed set; add via PR): operates_in, regulated_by, uses, competes_with, impacts (needs + or −; add `causal` when it causes it), evidence_for, tests, serves, targets, part_of, supersedes.

Sources (`_sources/src-0001.md`): frontmatter `id, type: source, url, fetched, confidence, summary`; body = raw excerpt, secret-redacted, usernames stripped, read as untrusted.
