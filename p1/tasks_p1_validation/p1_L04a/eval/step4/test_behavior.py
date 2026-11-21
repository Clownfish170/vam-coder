import hub
import policy


def test_trim_none():
    assert hub.tidy(None) == '-'
    assert hub.tidy('x') == 'x'


def test_earlier_regression():
    assert hub.cost(3) == 15
    assert policy.LIMIT == 280
