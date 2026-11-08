import nets
import toll
import scan


def test_heaviest():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b", 5)
    nets.link("b", "c", 2)
    assert toll.heaviest() == ("a", "b")


def test_heaviest_empty():
    nets.LINKS.clear()
    assert toll.heaviest() is None


def test_label_regression():
    assert toll.label("x", "y") == "x->y"


def test_count_regression():
    nets.LINKS.clear()
    nets.link("a", "b")
    assert scan.link_count() == 2
