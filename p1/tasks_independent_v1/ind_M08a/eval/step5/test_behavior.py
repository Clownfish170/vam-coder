import registry


def test_registration_order():
    registry.COMMANDS.clear()
    registry.ORDER.clear()
    registry.register("zebra", lambda a: 1)
    registry.register("alpha", lambda a: 2)
    assert registry.names() == ["zebra", "alpha"]


def test_dispatch_still_works():
    assert registry.dispatch("zebra", "") == 1


def test_unknown_regression():
    import pytest
    with pytest.raises(registry.UnknownCommand):
        registry.dispatch("ghost", "")
