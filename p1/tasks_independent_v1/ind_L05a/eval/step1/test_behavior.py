import mesh


def test_has_node():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_node("a")
    assert mesh.has_node("a") is True
    assert mesh.has_node("zz") is False


def test_add_node_regression():
    mesh.NODES.clear()
    mesh.add_node("a")
    mesh.add_node("a")
    assert mesh.NODES == ["a"]
