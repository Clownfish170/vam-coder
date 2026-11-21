import registry


def test_none_becomes_ok():
    registry.register("silent", lambda a: None)
    assert registry.dispatch("silent", 1) == "ok"


def test_passthrough():
    registry.register("loud", lambda a: a * 2)
    assert registry.dispatch("loud", 3) == 6


def test_alias_regression():
    registry.register("g2", lambda a: "g")
    registry.register_alias("a2", "g2")
    assert registry.dispatch("a2", None) == "g"
