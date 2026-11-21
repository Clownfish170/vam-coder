import helpers


def test_h2():
    assert helpers.h2() == 20


def test_others():
    assert helpers.h1() == 1 and helpers.h3() == 3
