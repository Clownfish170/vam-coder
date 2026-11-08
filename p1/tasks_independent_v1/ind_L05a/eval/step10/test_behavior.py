import costs
import mesh
import walk


def test_default_w_updated():
    assert costs.DEFAULT_W == 5
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    assert mesh.weight("a", "b") == 5


def test_set_w_still_wins():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    costs.set_w("a", "b", 9)
    assert mesh.weight("a", "b") == 9


def test_full_chain():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    costs.EDGE_W.clear()
    for n in ("a", "b", "c"):
        mesh.add_node(n)
    assert mesh.has_node("a") is True
    assert mesh.add_edge("a", "b") is True
    assert mesh.add_edge("a", "b") is False
    mesh.add_edge("a", "c")
    assert mesh.connected("a", "c") is True
    assert walk.dfs("a") == ["a", "b", "c"]
    assert walk.degree_line("a") == "a=2"
