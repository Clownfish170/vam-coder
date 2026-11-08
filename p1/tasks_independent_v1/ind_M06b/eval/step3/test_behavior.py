import billrun


def test_sub():
    assert billrun.run("8-3") == 5
    assert billrun.run("7 - 2") == 5


def test_add_regression():
    assert billrun.run("8+3") == 11


def test_mixed():
    assert billrun.run("9-2+1") == 8
