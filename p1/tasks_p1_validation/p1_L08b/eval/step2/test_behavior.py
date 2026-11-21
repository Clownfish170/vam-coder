from leaf import render_n
from mid import gate, gate_x2


def test_mid_x2():
    assert gate_x2(3) == 18
    assert gate_x2(-2) == -2


def test_mid_base():
    assert gate(3) == 10
