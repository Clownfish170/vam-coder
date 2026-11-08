import hub
import policy


def test_trim_none():
    assert hub.fix_tax(None) == '-'
    assert hub.fix_tax('x') == 'x'


def test_earlier_regression():
    assert hub.compute(3) == 12
    assert policy.LIMIT == 290
