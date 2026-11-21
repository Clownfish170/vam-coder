import billrun


def test_multi_scan():
    assert billrun.scan("25+13") == ["25", "+", "13"]


def test_multi_run():
    assert billrun.run("25+13") == 38
    assert billrun.run("100 - 40") == 60


def test_single_regression():
    assert billrun.run("8-3") == 5
