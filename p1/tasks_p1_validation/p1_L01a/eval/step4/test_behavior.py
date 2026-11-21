import hub
import policy


def test_trim_none():
    assert hub.trim(None) == '-'
    assert hub.trim('x') == 'x'


def test_earlier_regression():
    assert hub.quote(3) == 9
    assert policy.LIMIT == 250
