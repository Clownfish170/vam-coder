import panel


def test_count():
    panel.PLUGINS.clear()
    panel.plug("a", lambda: 1)
    panel.plug("b", lambda: 2)
    assert panel.count() == 2


def test_count_empty():
    panel.PLUGINS.clear()
    assert panel.count() == 0


def test_plug_regression():
    panel.PLUGINS.clear()
    panel.plug("a", lambda: 1)
    assert len(panel.PLUGINS) == 1
