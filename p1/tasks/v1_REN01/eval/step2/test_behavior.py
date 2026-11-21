import core, main


def test_bump3():
    assert core.bump(4) == 11


def test_run3():
    assert main.run(4) == 11
