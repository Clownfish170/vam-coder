import pytest
import pipeline


def test_unknown_stage():
    with pytest.raises(ValueError):
        pipeline.run(["a"], ["nope"])


def test_known_still_works():
    assert pipeline.run(["a", ""], ["load", "clean"]) == ["a"]


def test_default_regression():
    assert pipeline.default_stages() == ["load", "clean"]
