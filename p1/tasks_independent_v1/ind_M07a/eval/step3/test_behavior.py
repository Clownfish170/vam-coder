import pipeline


def test_trim_stage():
    assert pipeline.run(["  a  ", 3], ["trim"]) == ["a", 3]


def test_unknown_regression():
    import pytest
    with pytest.raises(ValueError):
        pipeline.run(["a"], ["nope"])


def test_clean_regression():
    assert pipeline.run(["a", " "], ["trim", "clean"]) == ["a"]
