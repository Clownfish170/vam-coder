import panel
import pre


def _seed():
    panel.PLUGINS.clear()
    panel.ALIASES.clear()
    pre.BEFORE.clear()
    panel.plug("danger", lambda: "ran")


def test_hook_blocks():
    _seed()
    pre.on_before(lambda name: False)
    assert panel.run("danger") is None


def test_hook_pass():
    _seed()
    pre.on_before(lambda name: True)
    assert panel.run("danger") == "ran"


def test_silent_regression():
    _seed()
    panel.SILENT = True
    assert panel.run("missing") is None
