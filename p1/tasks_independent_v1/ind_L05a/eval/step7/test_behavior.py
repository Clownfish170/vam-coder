import mesh
import walk


def _chain():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    for n in ("a", "b", "c"):
        mesh.add_node(n)
    mesh.add_edge("a", "b")
    mesh.add_edge("b", "c")


def test_connected_yes():
    _chain()
    assert mesh.connected("a", "c") is True


def test_connected_no():
    _chain()
    assert mesh.connected("c", "a") is False


def test_connected_self():
    _chain()
    assert mesh.connected("c", "c") is True


def test_bfs_regression():
    _chain()
    assert walk.bfs("a") == ["a", "b", "c"]
