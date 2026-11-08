from scoring import pick_rank
from scoring_rules import pick_rank as rules_pick_rank


def test_empty():
    assert pick_rank([]) is None


def test_target_returns_largest():
    assert pick_rank(['b', 'a', 'c']) == 'c'


def test_rules_companion_also_largest():
    assert rules_pick_rank(['b', 'a', 'c']) == 'c'
