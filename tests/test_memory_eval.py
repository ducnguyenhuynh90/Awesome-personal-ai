from evals.memory.run import run


def test_memory_eval_baseline_and_kb_restored():
    from robin.kb import schema
    before = schema.KB
    res = run()
    assert schema.KB == before                        # eval must not leave the KB pointed at the fixture
    assert res["recall"] >= 0.9 and res["precision"] >= 0.8   # baseline 2026-11-13: P 0.88, R 1.00
    assert len(res["rows"]) == 12
