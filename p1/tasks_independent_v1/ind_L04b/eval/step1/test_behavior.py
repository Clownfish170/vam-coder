import counter


def test_get():
    counter.VALUE = 5
    assert counter.get() == 5


def test_bump_regression():
    counter.VALUE = 0
    counter.bump(3)
    assert counter.VALUE == 3
