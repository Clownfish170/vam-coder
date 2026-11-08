import pytest
import panel
import pre
import cli


def _seed():
    panel.PLUGINS.clear()
    panel.ALIASES.clear()
    pre.BEFORE.clear()


def test_silent_default_true():
    _seed()
    assert panel.SILENT is True
    assert panel.run("missing") is None


def test_strict_override():
    _seed()
    panel.SILENT = False
    with pytest.raises(KeyError):
        panel.run("missing")


def test_full_chain():
    _seed()
    panel.plug("greet", lambda n: f"hi {n}", prio=2)
    panel.plug("bye", lambda n: f"by {n}", prio=9)
    panel.alias("hey", "greet")
    seen = []
    pre.on_before(lambda name: seen.append(name))
    assert panel.run("hey", "bob") == "hi bob"
    assert seen == ["greet"]
    assert panel.run_all("z") == ["by z", "hi z"]
    assert cli.call("ghost") is None
    assert panel.count() == 2
