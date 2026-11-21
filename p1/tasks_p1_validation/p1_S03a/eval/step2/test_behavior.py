import core


def test_new_fn():
    assert core.norm_pair(2) == 8 + 2
    assert core.norm_pair(-1) == -1


def test_rule_regression():
    assert core.norm_score(-2) == 0
    assert core.norm_score(3) == 12


def test_aux_regression():
    assert core.__name__ == 'core'
