from packing_rules import canon_label
from packing import pick_pack


def test_fn2_spec():
    assert canon_label('  xy  ') == 'XY'


def test_picker_regression():
    assert pick_pack(['b', 'a', 'c']) == 'c'
