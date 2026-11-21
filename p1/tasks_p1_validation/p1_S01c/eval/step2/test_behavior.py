from routing_rules import normalize
from routing import pick_route


def test_fn2_spec():
    assert normalize('  xy  ') == 'xy'


def test_picker_regression():
    assert pick_route(['b', 'a', 'c']) == 'c'
