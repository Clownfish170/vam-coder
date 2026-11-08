import hub
import policy


def test_trim_none():
    assert hub.clean(None) == '-'
    assert hub.clean('x') == 'x'


def test_earlier_regression():
    assert hub.price(3) == 12
    assert policy.LIMIT == 300
