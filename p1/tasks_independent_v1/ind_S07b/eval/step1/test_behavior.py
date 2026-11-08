import window


def test_under_capacity():
    w = window.Window(3)
    w.push(1)
    w.push(2)
    assert w.values() == [1, 2]


def test_overflow():
    w = window.Window(3)
    for x in (1, 2, 3, 4, 5):
        w.push(x)
    assert w.values() == [3, 4, 5]


def test_repr_swapped():
    w = window.Window(3)
    assert isinstance(w.__dict__.get("ring"), list)
    assert len(w.ring) == 3
    assert "buf" not in w.__dict__
