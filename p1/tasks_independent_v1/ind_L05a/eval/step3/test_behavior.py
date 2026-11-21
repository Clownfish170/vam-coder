import mesh
import costs


def test_weight_set():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    costs.set_w("a", "b", 5)
    assert mesh.weight("a", "b") == 5


def test_weight_default():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    assert mesh.weight("a", "b") == 1


def test_weight_missing_edge():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    assert mesh.weight("x", "y") is None


def test_dedup_regression():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    assert mesh.add_edge("a", "b") is True
    assert mesh.add_edge("a", "b") is False
