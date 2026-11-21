import bill


def test_due_fast():
    assert bill.due_fast(2) == 13


def test_due():
    assert bill.due(2) == 13
