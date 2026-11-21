import hub
import policy


def test_trim_none():
    assert hub.norm(None) == '-'
    assert hub.norm('x') == 'x'


def test_earlier_regression():
    assert hub.scale(3) == 6
    assert policy.LIMIT == 200
