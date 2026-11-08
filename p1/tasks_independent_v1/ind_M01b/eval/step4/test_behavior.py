import pytest

import grades


def test_zero_total():
    with pytest.raises(ValueError):
        grades.pct(5, 0)


def test_negative_total():
    with pytest.raises(ValueError):
        grades.pct(5, -1)


def test_ok_regression():
    assert grades.pct(9, 10) == 90.0
