import nets
import toll
import scan


def test_directed_link():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("x", "y", 3)
    assert nets.LINKS[("x", "y")] == 3
    assert ("y", "x") not in nets.LINKS


def test_directed_heaviest():
    nets.LINKS.clear()
    nets.link("a", "b", 5)
    assert toll.heaviest() == ("a", "b")


def test_count_regression():
    nets.LINKS.clear()
    nets.link("a", "b")
    assert scan.link_count() == 1


def test_weight_regression():
    nets.LINKS.clear()
    nets.link("a", "b", 4)
    assert nets.weight("a", "b") == 4
    assert nets.weight("b", "a") is None
