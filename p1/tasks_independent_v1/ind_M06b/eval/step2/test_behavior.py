import billrun


def test_add():
    assert billrun.run("8+3") == 11
    assert billrun.run("4 + 5") == 9


def test_single():
    assert billrun.run("7") == 7


def test_scan_regression():
    assert billrun.scan("8+3") == ["8", "+", "3"]
