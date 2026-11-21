import core


def test_new_fn():
    assert core.scale_pair(2) == 12 + 2
    assert core.scale_pair(-1) == -1


def test_rule_regression():
    assert core.scale_w(-2) == 0
    assert core.scale_w(3) == 18


def test_aux_regression():
    assert core.__name__ == 'core'
