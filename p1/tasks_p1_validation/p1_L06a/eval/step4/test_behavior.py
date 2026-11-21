import hub
import policy


def test_trim_none():
    assert hub.scrub(None) == '-'
    assert hub.scrub('x') == 'x'


def test_earlier_regression():
    assert hub.fee_of(3) == 9
    assert policy.LIMIT == 260
