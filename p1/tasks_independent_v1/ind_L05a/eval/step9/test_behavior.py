import mesh
import walk
import costs


def test_dfs_order():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    for n in ("a", "b", "c", "d"):
        mesh.add_node(n)
    mesh.add_edge("a", "b")
    mesh.add_edge("a", "c")
    mesh.add_edge("b", "d")
    assert walk.dfs("a") == ["a", "b", "d", "c"]


def test_old_name_gone():
    assert not hasattr(walk, "bfs")


def test_default_w_regression():
    assert costs.DEFAULT_W == 2
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    assert mesh.weight("a", "b") == 2
