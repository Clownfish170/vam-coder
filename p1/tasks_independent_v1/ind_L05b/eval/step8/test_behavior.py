import nets


def test_cap_constant():
    assert nets.CAP == 6


def test_capped():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b", 9)
    assert nets.capped("a", "b") == 6
    nets.link("b", "c", 2)
    assert nets.capped("b", "c") == 2


def test_capped_missing():
    nets.LINKS.clear()
    assert nets.capped("x", "y") is None


def test_reachable_regression():
    nets.NODES.clear()
    nets.LINKS.clear()
    nets.link("a", "b")
    nets.link("b", "c")
    assert nets.reachable("a") == ["a", "b", "c"]
