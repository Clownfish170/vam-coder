import report
import store


def test_merge():
    assert store.merge_rows({'z': 7})['z'] == 7
    assert store.get_row('z') == 7


def test_run_regression():
    assert report.label_for(3) == 'fee: 18'
