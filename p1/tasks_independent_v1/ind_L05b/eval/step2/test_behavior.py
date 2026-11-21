import pytest
import nets


def test_self_loop_rejected():
    nets.NODES.clear()
    nets.LINKS.clear()
    with pytest.raises(ValueError):
        nets.link("a", "a")


def test_link_ok():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b")
    assert nets.LINKS[("a", "b")] is True
    assert nets.LINKS[("b", "a")] is True


def test_nodes_regression():
    nets.NODES.clear()
    nets.add_node("b")
    nets.add_node("a")
    assert nets.nodes() == ["a", "b"]
