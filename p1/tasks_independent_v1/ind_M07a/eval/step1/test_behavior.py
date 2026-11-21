import pipeline


def test_reads_config():
    assert pipeline.default_stages() == ["load", "clean"]


def test_run_uses_default():
    assert pipeline.run(["a", "", "b"]) == ["a", "b"]
