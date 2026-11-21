import billrun


def test_scan_ops():
    assert billrun.scan("8+3") == ["8", "+", "3"]
    assert billrun.scan("9-1") == ["9", "-", "1"]


def test_scan_spaces():
    assert billrun.scan("8 + 3") == ["8", "+", "3"]


def test_run_regression():
    assert billrun.run("7") == 7
