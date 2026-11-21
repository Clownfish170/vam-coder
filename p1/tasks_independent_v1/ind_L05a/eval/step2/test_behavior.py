import mesh


def test_add_edge_dedup():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    assert mesh.add_edge("a", "b") is True
    assert mesh.add_edge("a", "b") is False
    assert mesh.ADJ["a"] == ["b"]


def test_symmetric():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_edge("a", "b")
    assert mesh.ADJ["b"] == ["a"]


def test_has_node_regression():
    mesh.NODES.clear()
    mesh.add_node("a")
    assert mesh.has_node("a") is True
