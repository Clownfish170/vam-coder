import flow


def test_upper_stage():
    assert flow.execute(["ab", 5], ["upper"]) == ["AB", 5]


def test_unknown_regression():
    import pytest
    with pytest.raises(ValueError):
        flow.execute(["a"], ["nope"])


def test_dedupe_regression():
    assert flow.execute(["a", "a"], ["dedupe"]) == ["a"]
