from billing import pick_bill
from billing_rules import pick_bill as rules_pick_bill


def test_empty():
    assert pick_bill([]) is None


def test_target_returns_largest():
    assert pick_bill(['b', 'a', 'c']) == 'c'


def test_rules_companion_also_largest():
    assert rules_pick_bill(['b', 'a', 'c']) == 'c'
