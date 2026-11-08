import hub
import report


def test_run():
    assert report.desc_of(3) == 'fee: 9'


def test_trim_regression():
    assert hub.scrub(None) == '-'
