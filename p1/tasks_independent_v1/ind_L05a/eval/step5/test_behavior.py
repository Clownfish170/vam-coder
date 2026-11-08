import mesh
import costs


def test_directed_edge():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("x", "y")
    assert mesh.ADJ["x"] == ["y"]
    assert mesh.ADJ["y"] == []
    assert mesh.weight("y", "x") is None


def test_directed_dedup():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    assert mesh.add_edge("x", "y") is True
    assert mesh.add_edge("x", "y") is False


def test_degree_regression():
    import walk
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_edge("a", "b")
    mesh.add_edge("a", "c")
    assert walk.degree_line("a") == "a=2"
