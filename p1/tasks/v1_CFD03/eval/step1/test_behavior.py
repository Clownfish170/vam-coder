import pytest, util


def test_clamp_ok():
    assert util.clamp(1, 0, 10) == 1


def test_clamp_raises():
    with pytest.raises(ValueError):
        util.clamp(1, 5, 0)
