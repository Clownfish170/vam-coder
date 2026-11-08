import hub
import report


def test_run():
    assert report.show(3) == 'fee: 12'


def test_trim_regression():
    assert hub.clean(None) == '-'
