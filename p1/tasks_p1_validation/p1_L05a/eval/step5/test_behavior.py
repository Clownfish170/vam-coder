import hub
import report


def test_run():
    assert report.label_for(3) == 'fee: 18'


def test_trim_regression():
    assert hub.fix(None) == '-'
