"""Knowledge base as in-process MCP tools (server name 'kb' -> tools mcp__kb__*).

Agents write knowledge through these typed tools, never through a shell. Every
write goes through robin.kb.writer (lock, secret redaction, changelog) and the
result reports `kb lint` problems for the touched node so the agent fixes them.
"""
from __future__ import annotations

from robin.kb import lint, query, writer
from robin.kb.writer import KBWriteError


def _ok(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _err(text: str) -> dict:
    return {"content": [{"type": "text", "text": f"ERROR: {text}"}], "is_error": True}


def _lint_for(node_id: str) -> str:
    problems = [e for e in lint.lint() if f"/{node_id}.md" in e]
    return "lint: OK" if not problems else "lint problems:\n" + "\n".join(problems)


def build_server():
    from claude_agent_sdk import create_sdk_mcp_server, tool

    @tool("query", "Find knowledge nodes. Returns id + one-line summary (read the file only if the summary is not enough).",
          {"text": str, "near": str, "hops": int, "market": str, "type": str})
    async def kb_query(args):
        lines = query.query(near=args.get("near") or None, hops=int(args.get("hops") or 1),
                            market=args.get("market") or None, type_=args.get("type") or None,
                            text=args.get("text") or None)
        return _ok("\n".join(lines) or "no match")

    @tool("add_source", "Store a source excerpt (graded A/B/C). Returns its src-id. Excerpt is redacted for secrets and personal handles.",
          {"url": str, "excerpt": str, "grade": str, "summary": str})
    async def kb_add_source(args):
        try:
            return _ok(writer.add_source(args["url"], args["excerpt"], args["grade"], args["summary"], by="robin"))
        except (KBWriteError, KeyError) as e:
            return _err(str(e))

    @tool("add_fact", "Add one fact line to a node. Needs >= 1 existing src-id and a grade. No source -> use add_gap.",
          {"node_id": str, "fact": str, "sources": list, "grade": str, "inferred": bool})
    async def kb_add_fact(args):
        try:
            writer.add_fact(args["node_id"], args["fact"], list(args.get("sources") or []), args["grade"],
                            inferred=bool(args.get("inferred")), by="robin")
            return _ok("added. " + _lint_for(args["node_id"]))
        except (KBWriteError, KeyError) as e:
            return _err(str(e))

    @tool("new_node", "Create a node (market, competitor, metric, product, ...). id must be a lowercase slug, e.g. market-ph.",
          {"node_id": str, "type": str, "summary": str, "markets": list})
    async def kb_new(args):
        try:
            path = writer.create_node(args["node_id"], args["type"], args["summary"], markets=args.get("markets"))
            return _ok(f"created {path.name}")
        except (KBWriteError, KeyError) as e:
            return _err(str(e))

    @tool("add_gap", "Record something we do not know: the question, what was tried, what to try next.",
          {"question": str, "tried": str, "next": str})
    async def kb_gap(args):
        writer.add_gap(args["question"], args.get("tried", ""), args.get("next", ""))
        return _ok("recorded in knowledge/_gaps.md")

    return create_sdk_mcp_server("kb", tools=[kb_query, kb_add_source, kb_add_fact, kb_new, kb_gap])
