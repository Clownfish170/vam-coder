import flow


def test_reads_settings():
    assert flow.default_flow() == ["read", "dedupe"]


def test_execute_uses_default():
    assert flow.execute(["a", "a", "b"]) == ["a", "b"]
