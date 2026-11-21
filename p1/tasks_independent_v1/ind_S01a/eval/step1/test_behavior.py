import stats


def test_odd():
    assert stats.median([3, 1, 2]) == 2


def test_even():
    assert stats.median([1, 2, 3, 4]) == 2.5


def test_negative():
    assert stats.median([-4, -2]) == -3
