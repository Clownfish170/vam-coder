import nets


def test_nodes_sorted():
    nets.NODES.clear()
    nets.add_node("b")
    nets.add_node("a")
    assert nets.nodes() == ["a", "b"]


def test_nodes_empty():
    nets.NODES.clear()
    assert nets.nodes() == []


def test_add_node_regression():
    nets.NODES.clear()
    nets.add_node("x")
    assert "x" in nets.NODES
