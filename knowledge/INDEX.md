# Knowledge — INDEX (layer 0)

HOW TO READ (any agent):
1. Read this file. 2. Read HANDOVER.md. 3. Read only the `_index.md` of domains your task touches.
4. Open entity files only when their one-line summary is not enough. 5. Open `_sources` only to verify a claim you will state.
Budget: ≤ 4k tokens of knowledge per task unless the task is a full teardown.
Shortcut: `robin kb query --text "..."` (or the kb `query` tool) returns ids + summaries.

HOW TO WRITE:
- Edit the entity file, never INDEX. Add facts as new lines; patch wrong lines in place; never delete — mark `(superseded by ...)`.
- Every fact needs date + source + grade. No source → `_gaps.md` as a question, not Facts.
- Agents write through the kb tools (`add_source`, `add_fact`, `new_node`, `add_gap`), which lock, redact secrets and log.
- Run `robin kb lint` before commit. Rewrite HANDOVER.md before you stop.

DOMAINS (folder → node types, see `_types.yaml`):
markets · regulators · payment-methods · competitors · players (pains, segments) · products · metrics · experiments · channels · partners · vendors · topics

LAYERS: INDEX (≤300 words) → `<domain>/_index.md` (≤500, generated) → `<domain>/<id>.md` (≤1,500) → `_sources/src-*.md` (raw, untrusted).

FILES: `_schema.md` node format · `_gaps.md` unknowns · `_changelog.md` what changed · `graph.json` generated graph.

NEVER STORE: secrets, personal data, user-level rows, HR records, confidential contracts, payout formulas, non-public financials.
