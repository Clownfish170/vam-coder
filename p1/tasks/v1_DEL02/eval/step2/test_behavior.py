import worker


def test_drain():
    items = [1, 2, 3]
    assert worker.drain(items) == 3
    assert items == []
