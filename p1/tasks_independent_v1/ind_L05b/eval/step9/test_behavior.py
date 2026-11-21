import nets


def _chain():
    nets.NODES.clear()
    nets.LINKS.clear()
    for n in ("a", "b", "c", "d"):
        nets.add_node(n)
    nets.link("a", "b")
    nets.link("b", "c")
    nets.link("c", "d")


def test_reachable_two_hops():
    _chain()
    assert nets.reachable("a") == ["a", "b", "c"]


def test_reachable_one_hop():
    _chain()
    assert nets.reachable("c") == ["c", "d"]


def test_cap_regression():
    nets.LINKS.clear()
    nets.link("a", "b", 9)
    assert nets.capped("a", "b") == 6
