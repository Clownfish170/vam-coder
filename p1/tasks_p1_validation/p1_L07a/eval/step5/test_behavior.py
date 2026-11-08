import hub
import report


def test_run():
    assert report.line_of(3) == 'fee: 6'


def test_trim_regression():
    assert hub.tidy_i(None) == '-'
