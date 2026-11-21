from leaf import fold
from mid import step, step_x2


def test_mid_x2():
    assert step_x2(3) == 27
    assert step_x2(-2) == -3


def test_mid_base():
    assert step(3) == 10
