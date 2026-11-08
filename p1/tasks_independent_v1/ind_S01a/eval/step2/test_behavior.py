import pytest

import stats


def test_empty():
    with pytest.raises(ValueError):
        stats.median([])


def test_even_regression():
    assert stats.median([1, 2, 3, 4]) == 2.5


def test_odd_regression():
    assert stats.median([3, 1, 2]) == 2
