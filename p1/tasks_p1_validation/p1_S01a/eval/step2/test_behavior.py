import core


def test_new_fn():
    assert core.adjust_pair(2) == 10 + 2
    assert core.adjust_pair(-1) == -1


def test_rule_regression():
    assert core.adjust(-2) == 0
    assert core.adjust(3) == 15


def test_aux_regression():
    assert core.__name__ == 'core'
