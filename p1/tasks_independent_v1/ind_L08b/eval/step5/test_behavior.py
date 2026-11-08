import pytest
import panel
import cli


def _seed():
    panel.PLUGINS.clear()
    panel.ALIASES.clear()
    panel.plug("greet", lambda: "hi")


def test_alias_run():
    _seed()
    panel.alias("hi", "greet")
    assert panel.run("hi") == "hi"


def test_alias_target_missing():
    _seed()
    with pytest.raises(KeyError):
        panel.alias("x", "ghost")


def test_call_regression():
    _seed()
    assert cli.call("greet") == "hi"
