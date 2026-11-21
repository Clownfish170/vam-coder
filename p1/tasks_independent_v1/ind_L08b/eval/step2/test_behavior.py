import pytest
import panel


def test_run():
    panel.PLUGINS.clear()
    panel.plug("double", lambda x: x * 2)
    assert panel.run("double", 5) == 10


def test_run_missing():
    panel.PLUGINS.clear()
    with pytest.raises(KeyError):
        panel.run("nope")


def test_count_regression():
    panel.PLUGINS.clear()
    panel.plug("a", lambda: 1)
    assert panel.count() == 1
