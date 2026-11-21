import lib, app


def test_dead_gone():
    assert not hasattr(lib, 'dead')


def test_keep():
    assert lib.keep() == 21
