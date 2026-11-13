import asyncio

from robin import orchestrator as o


def test_short_output_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(o, "OUTBOX", tmp_path)
    out, info = asyncio.run(o.enforce_cap("Yes. GCash.", "t-1"))
    assert out == "Yes. GCash." and info == {"capped": False}


def test_long_output_trimmed_and_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(o, "OUTBOX", tmp_path)
    monkeypatch.setattr(o, "ROOT", tmp_path.parent)
    long = "Line one answers the ask.\n" + "\n".join(f"- detail {i} " + "word " * 12 for i in range(30))
    out, info = asyncio.run(o.enforce_cap(long, "t-2"))
    assert o._words(out) <= 120
    assert out.startswith("Line one answers the ask.")
    assert out.rstrip().endswith("outbox/t-2-full.md")
    assert (tmp_path / "t-2-full.md").read_text() == long
    assert info["method"] == "trim" and info["words_before"] > 120


def test_rewrite_used_when_valid_and_trim_when_not(tmp_path, monkeypatch):
    monkeypatch.setattr(o, "OUTBOX", tmp_path)
    monkeypatch.setattr(o, "ROOT", tmp_path.parent)
    long = "word " * 300

    async def good(text, cap, link):
        return "Short answer.\n" + link

    async def bad(text, cap, link):
        return "word " * 200  # over cap and no link

    out, info = asyncio.run(o.enforce_cap(long, "t-3", shorten=good))
    assert info["method"] == "rewrite" and out.startswith("Short answer.")
    out, info = asyncio.run(o.enforce_cap(long, "t-4", shorten=bad))
    assert info["method"] == "trim" and o._words(out) <= 120
