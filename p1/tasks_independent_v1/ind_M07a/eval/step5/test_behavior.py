import pipeline


def test_new_default():
    assert pipeline.default_stages() == [
        "load", "trim", "clean"]


def test_run_with_new_default():
    out = pipeline.run(["  a  ", "", " b "])
    assert out == ["a", "b"]


def test_count_regression():
    assert pipeline.run(["a", "b"], ["count"]) == [2]
