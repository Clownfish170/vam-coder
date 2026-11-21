import pytest
import flow


def test_unknown_flow():
    with pytest.raises(ValueError):
        flow.execute(["a"], ["nope"])


def test_known_still_works():
    assert flow.execute(["x", "x"], ["dedupe"]) == ["x"]


def test_default_regression():
    assert flow.default_flow() == ["read", "dedupe"]
