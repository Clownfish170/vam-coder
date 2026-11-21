from scoring_rules import round_note
from scoring import pick_rank


def test_fn2_spec():
    assert round_note('3.14159') == '3.1'


def test_picker_regression():
    assert pick_rank(['b', 'a', 'c']) == 'c'
