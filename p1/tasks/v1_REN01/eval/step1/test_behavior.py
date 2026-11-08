import core, main


def test_double_value():
    assert core.double_value(4) == 8


def test_old_gone():
    assert not hasattr(core, 'double')


def test_bump():
    assert core.bump(4) == 9


def test_run():
    assert main.run(4) == 9
