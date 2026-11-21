import nets


def _chain():
    nets.NODES.clear()
    nets.LINKS.clear()
    for n in ("a", "b", "c", "d"):
        nets.add_node(n)
    nets.link("a", "b")
    nets.link("b", "c")
    nets.link("c", "d")


def test_reachable_full():
    _chain()
    assert nets.reachable("a") == ["a", "b", "c", "d"]


def test_reachable_backward():
    _chain()
    assert nets.reachable("d") == ["d"]


def test_directed_regression():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("x", "y", 3)
    assert ("y", "x") not in nets.LINKS
