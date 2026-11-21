from packing import pick_pack
from packing_rules import pick_pack as rules_pick_pack


def test_empty():
    assert pick_pack([]) is None


def test_target_returns_largest():
    assert pick_pack(['b', 'a', 'c']) == 'c'


def test_rules_companion_also_largest():
    assert rules_pick_pack(['b', 'a', 'c']) == 'c'
