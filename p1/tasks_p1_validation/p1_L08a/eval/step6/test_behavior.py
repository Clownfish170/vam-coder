import report
import store


def test_merge():
    assert store.merge_tax({'z': 7})['z'] == 7
    assert store.get_tax('z') == 7


def test_run_regression():
    assert report.tax_run(3) == 'fee: 12'
