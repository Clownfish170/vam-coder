import pipeline


def test_run_label():
    assert pipeline.run("x") == "v2:x"


def test_run_all_regression():
    assert pipeline.run_all(["a", "b"]) == ["v2:a", "v2:b"]
