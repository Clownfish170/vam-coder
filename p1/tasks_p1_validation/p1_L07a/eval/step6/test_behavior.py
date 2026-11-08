import report
import store


def test_merge():
    assert store.merge_i({'z': 7})['z'] == 7
    assert store.load_i('z') == 7


def test_run_regression():
    assert report.line_of(3) == 'fee: 6'
