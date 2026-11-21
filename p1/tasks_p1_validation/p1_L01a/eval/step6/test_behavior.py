import report
import store


def test_merge():
    assert store.merge({'z': 7})['z'] == 7
    assert store.get('z') == 7


def test_run_regression():
    assert report.run(3) == 'fee: 9'
