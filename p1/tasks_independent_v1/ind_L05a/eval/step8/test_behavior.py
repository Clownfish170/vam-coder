import costs
import mesh


def test_default_w_constant():
    assert costs.DEFAULT_W == 2


def test_weight_uses_default():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    assert mesh.weight("a", "b") == 2


def test_connected_regression():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_edge("a", "b")
    assert mesh.connected("a", "b") is True
    assert mesh.connected("b", "a") is False
