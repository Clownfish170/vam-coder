import registry


def test_alias():
    registry.register("greet", lambda a: "hola " + a)
    registry.register_alias("hi2", "greet")
    assert registry.dispatch("hi2", "bob") == "hola bob"


def test_unknown_regression():
    import pytest
    with pytest.raises(registry.UnknownCommand):
        registry.dispatch("nope", "")
