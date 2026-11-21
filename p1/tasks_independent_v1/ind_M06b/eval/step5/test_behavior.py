import billrun


def test_mul():
    assert billrun.run("6*7") == 42
    assert billrun.run("5 * 8") == 40


def test_chain():
    assert billrun.run("2+3*4") == 20


def test_multi_regression():
    assert billrun.run("25+13") == 38
