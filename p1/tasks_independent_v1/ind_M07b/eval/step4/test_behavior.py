import flow


def test_total_stage():
    assert flow.execute([1, 2, 3], ["total"]) == [6]


def test_total_ignores_non_numeric():
    assert flow.execute([1, "x", 2], ["total"]) == [3]


def test_upper_regression():
    assert flow.execute(["ab"], ["upper"]) == ["AB"]
