import pipeline


def test_count_stage():
    assert pipeline.run(["a", "b", "c"], ["count"]) == [3]


def test_count_after_clean():
    assert pipeline.run(["a", ""], ["clean", "count"]) == [1]


def test_trim_regression():
    assert pipeline.run(["  x "], ["trim"]) == ["x"]
