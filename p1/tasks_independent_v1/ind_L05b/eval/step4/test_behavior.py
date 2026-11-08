import nets
import scan


def test_link_count():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b", 2)
    assert scan.link_count() == 2


def test_link_count_empty():
    nets.LINKS.clear()
    assert scan.link_count() == 0


def test_tag_regression():
    assert scan.tag() == "scan"


def test_weight_regression():
    nets.LINKS.clear()
    nets.link("a", "b", 3)
    assert nets.weight("a", "b") == 3
