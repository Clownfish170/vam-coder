import window


def test_size():
    w = window.Window(3)
    w.push(1)
    w.push(2)
    assert w.size() == 2
    w.push(3)
    w.push(4)
    assert w.size() == 3


def test_repr_regression():
    w = window.Window(3)
    assert isinstance(w.__dict__.get("ring"), list)
    assert "buf" not in w.__dict__


def test_values_regression():
    w = window.Window(2)
    w.push(1)
    w.push(2)
    w.push(3)
    assert w.values() == [2, 3]
