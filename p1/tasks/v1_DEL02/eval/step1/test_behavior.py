import queue as qmod


def test_q_gone():
    assert not hasattr(qmod, 'q')


def test_p_exists():
    assert hasattr(qmod, 'p')
