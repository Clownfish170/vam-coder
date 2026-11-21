import mesh
import walk


def test_degree_line():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_edge("a", "b")
    mesh.add_edge("a", "c")
    assert walk.degree_line("a") == "a=2"


def test_degree_zero():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    mesh.add_node("solo")
    assert walk.degree_line("solo") == "solo=0"


def test_tag_regression():
    assert walk.tag() == "walk"


def test_weight_regression():
    mesh.NODES.clear()
    mesh.ADJ.clear()
    import costs
    costs.EDGE_W.clear()
    mesh.add_edge("a", "b")
    assert mesh.weight("a", "b") == 1
