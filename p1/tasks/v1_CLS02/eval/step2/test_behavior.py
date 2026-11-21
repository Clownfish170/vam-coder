import a, b, c


def test_b_plus1():
    assert b.fb(2) == 7


def test_ac_unchanged():
    assert a.fa(2) == 6
    assert c.fc(2) == 6
