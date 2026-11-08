import invoice


def test_batch():
    rows = [(100, 3, 10), (600, 10, 10)]
    assert invoice.batch_total(rows) == 78.0


def test_batch_empty():
    assert invoice.batch_total([]) == 0


def test_order_regression():
    assert invoice.order_total(100, 3, 10) == 18.0
