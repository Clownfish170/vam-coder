import hub
import report


def test_run():
    assert report.emit(3) == 'fee: 6'


def test_trim_regression():
    assert hub.norm(None) == '-'
