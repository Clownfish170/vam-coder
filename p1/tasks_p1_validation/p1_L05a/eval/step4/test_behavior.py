import hub
import policy


def test_trim_none():
    assert hub.fix(None) == '-'
    assert hub.fix('x') == 'x'


def test_earlier_regression():
    assert hub.points(3) == 18
    assert policy.LIMIT == 220
