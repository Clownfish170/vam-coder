import nets


def test_link_weight():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b", 4)
    assert nets.weight("a", "b") == 4
    assert nets.weight("b", "a") == 4


def test_weight_default():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b")
    assert nets.weight("a", "b") == 1


def test_weight_missing():
    nets.NODES.clear()
    nets.LINKS.clear()
    assert nets.weight("x", "y") is None


def test_self_loop_regression():
    import pytest
    nets.LINKS.clear()
    with pytest.raises(ValueError):
        nets.link("a", "a")
