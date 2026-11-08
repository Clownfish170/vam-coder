import hub
import report


def test_run():
    assert report.entry_of(3) == 'fee: 15'


def test_trim_regression():
    assert hub.tidy(None) == '-'
