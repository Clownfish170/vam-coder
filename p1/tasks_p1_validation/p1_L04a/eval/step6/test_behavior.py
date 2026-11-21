import report
import store


def test_merge():
    assert store.join({'z': 7})['z'] == 7
    assert store.peek('z') == 7


def test_run_regression():
    assert report.entry_of(3) == 'fee: 15'
