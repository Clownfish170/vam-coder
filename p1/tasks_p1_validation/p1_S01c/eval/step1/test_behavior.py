from routing import pick_route
from routing_rules import pick_route as rules_pick_route


def test_empty():
    assert pick_route([]) is None


def test_target_returns_largest():
    assert pick_route(['b', 'a', 'c']) == 'c'


def test_rules_companion_also_largest():
    assert rules_pick_route(['b', 'a', 'c']) == 'c'
