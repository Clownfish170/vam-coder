import panel
import pre


def _seed():
    panel.PLUGINS.clear()
    panel.ALIASES.clear()
    pre.BEFORE.clear()
    panel.plug("echo", lambda x: x * 3)


def test_before_hooks():
    _seed()
    seen = []
    pre.on_before(lambda name: seen.append(name))
    assert panel.run("echo", 4) == 12
    assert seen == ["echo"]


def test_no_hooks():
    _seed()
    assert panel.run("echo", 2) == 6


def test_alias_regression():
    _seed()
    panel.alias("e", "echo")
    assert panel.run("e", 1) == 3
