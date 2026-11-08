import pytest
import panel
import pre


def _seed():
    panel.PLUGINS.clear()
    panel.ALIASES.clear()
    pre.BEFORE.clear()


def test_silent_false_default():
    _seed()
    assert panel.SILENT is False
    with pytest.raises(KeyError):
        panel.run("missing")


def test_silent_true():
    _seed()
    panel.SILENT = True
    assert panel.run("missing") is None


def test_registered_works():
    _seed()
    panel.plug("r", lambda: 5)
    assert panel.run("r") == 5
