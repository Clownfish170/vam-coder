import hub
import policy


def test_trim_none():
    assert hub.tidy_i(None) == '-'
    assert hub.tidy_i('x') == 'x'


def test_earlier_regression():
    assert hub.interest(3) == 6
    assert policy.LIMIT == 320
