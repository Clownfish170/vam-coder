import report
import store


def test_merge():
    assert store.blend({'z': 7})['z'] == 7
    assert store.load('z') == 7


def test_run_regression():
    assert report.show(3) == 'fee: 12'
