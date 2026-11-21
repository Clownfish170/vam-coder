import mesh
import walk


def test_bfs():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    for n in ("a", "b", "c", "d"):
        mesh.add_node(n)
    mesh.add_edge("a", "b")
    mesh.add_edge("a", "c")
    mesh.add_edge("b", "d")
    assert walk.bfs("a") == ["a", "b", "c", "d"]


def test_bfs_isolated():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_node("solo")
    assert walk.bfs("solo") == ["solo"]


def test_directed_regression():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_edge("x", "y")
    assert mesh.ADJ["y"] == []
