import report
import store


def test_merge():
    assert store.fold({'z': 7})['z'] == 7
    assert store.fetch('z') == 7


def test_run_regression():
    assert report.emit(3) == 'fee: 6'
