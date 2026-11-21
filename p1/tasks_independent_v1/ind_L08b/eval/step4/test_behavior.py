import panel
import cli


def test_call_ok():
    panel.PLUGINS.clear()
    panel.plug("echo", lambda x: f"got:{x}")
    assert cli.call("echo", "hi") == "got:hi"


def test_call_missing():
    panel.PLUGINS.clear()
    assert cli.call("nope") is None


def test_banner_regression():
    assert cli.banner() == "cli"


def test_count_regression():
    panel.PLUGINS.clear()
    panel.plug("a", lambda: 1)
    assert panel.count() == 1
