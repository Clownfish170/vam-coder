from billing_rules import tag_clean
from billing import pick_bill


def test_fn2_spec():
    assert tag_clean('  xy  ') == 'ok:xy'


def test_picker_regression():
    assert pick_bill(['b', 'a', 'c']) == 'c'
