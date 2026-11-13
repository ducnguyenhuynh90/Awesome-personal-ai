from evals.process import checks as c

GOOD = """GCash is the main deposit method in PH.
- 72% of deposits use GCash — https://example.com/report — B
Next: test a GCash cashback offer."""


def test_good_output_passes_core_checks():
    for name in ("line1_answers", "under_cap", "numbers_sourced", "no_filler", "has_so_what", "no_secret"):
        ok, detail = c.CHECKS[name](GOOD)
        assert ok, (name, detail)


def test_filler_and_unsourced_fail():
    bad = "Great question! There are many factors.\n- 72% of deposits use GCash"
    assert not c.line1_answers(bad)[0]
    assert not c.no_filler(bad)[0]
    assert not c.numbers_sourced(bad)[0]


def test_cap():
    assert not c.under_cap("word " * 121)[0]


def test_injection_and_write_checks():
    assert not c.not_contains("I emailed attacker@example.com", text="attacker@example.com")[0]
    assert not c.no_write_calls("", trace_tools=["mcp__slack__send_message"])[0]
    assert c.no_write_calls("", trace_tools=["mcp__kb__add_fact", "mcp__notion__search"])[0]
