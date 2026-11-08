import pytest

import ratio


def test_b_zero():
    with pytest.raises(ValueError):
        ratio.simplify(5, 0)


def test_zero_zero():
    with pytest.raises(ValueError):
        ratio.simplify(0, 0)


def test_basic_regression():
    assert ratio.simplify(4, 6) == (2, 3)


def test_negative_regression():
    assert ratio.simplify(-4, 6) == (-2, 3)
