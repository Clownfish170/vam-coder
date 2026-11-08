import report
import store


def test_merge():
    assert store.combine({'z': 7})['z'] == 7
    assert store.last('z') == 7


def test_run_regression():
    assert report.desc_of(3) == 'fee: 9'
