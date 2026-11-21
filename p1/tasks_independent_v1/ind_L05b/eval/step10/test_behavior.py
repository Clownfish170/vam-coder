import nets
import scan
import toll


def test_cap_updated():
    assert nets.CAP == 3
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b", 9)
    assert nets.capped("a", "b") == 3
    nets.link("b", "c", 2)
    assert nets.capped("b", "c") == 2


def test_full_chain():
    nets.NODES.clear()
    nets.LINKS.clear()
    for n in ("a", "b", "c"):
        nets.add_node(n)
    assert nets.nodes() == ["a", "b", "c"]
    nets.link("a", "b", 4)
    nets.link("b", "c", 7)
    assert scan.link_count() == 2
    assert toll.heaviest() == ("b", "c")
    assert nets.reachable("a") == ["a", "b", "c"]
    assert nets.capped("b", "c") == 3
