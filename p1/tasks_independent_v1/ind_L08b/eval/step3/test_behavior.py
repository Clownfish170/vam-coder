import pytest
import panel


def test_duplicate_rejected():
    panel.PLUGINS.clear()
    panel.plug("a", lambda: 1)
    with pytest.raises(ValueError):
        panel.plug("a", lambda: 2)
    assert panel.run("a") == 1


def test_new_name_ok():
    panel.PLUGINS.clear()
    panel.plug("a", lambda: 1)
    panel.plug("b", lambda: 2)
    assert panel.run("b") == 2


def test_run_regression():
    panel.PLUGINS.clear()
    panel.plug("double", lambda x: x * 2)
    assert panel.run("double", 5) == 10
