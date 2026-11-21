import pytest
import panel
import pre


def _seed():
    panel.PLUGINS.clear()
    panel.ALIASES.clear()
    pre.BEFORE.clear()


def test_run_all_priority():
    _seed()
    panel.plug("a", lambda: "A", prio=1)
    panel.plug("b", lambda: "B", prio=5)
    panel.plug("c", lambda: "C", prio=5)
    assert panel.run_all() == ["B", "C", "A"]


def test_run_still_works():
    _seed()
    panel.plug("x", lambda v: v + 1, prio=3)
    assert panel.run("x", 4) == 5


def test_duplicate_still_rejected():
    _seed()
    panel.plug("a", lambda: 1)
    with pytest.raises(ValueError):
        panel.plug("a", lambda: 2)


def test_before_regression():
    _seed()
    seen = []
    pre.on_before(lambda name: seen.append(name))
    panel.plug("echo", lambda: 5)
    panel.run("echo")
    assert seen == ["echo"]
