import core


def test_new_fn():
    assert core.tier_pair(2) == 14 + 2
    assert core.tier_pair(-1) == -1


def test_rule_regression():
    assert core.tier_of(-2) == 0
    assert core.tier_of(3) == 21


def test_aux_regression():
    assert core.__name__ == 'core'
