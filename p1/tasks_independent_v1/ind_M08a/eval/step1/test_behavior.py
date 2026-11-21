import pytest
import registry


def test_unknown():
    with pytest.raises(registry.UnknownCommand):
        registry.dispatch("zz", "")


def test_known():
    registry.register("t", lambda a: a)
    assert registry.dispatch("t", "x") == "x"


def test_names_regression():
    assert "t" in registry.names()
