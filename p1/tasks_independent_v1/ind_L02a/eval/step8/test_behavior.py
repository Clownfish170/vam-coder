import ledger


def test_boundary_inclusive():
    assert ledger.fee(100) == 100


def test_below_boundary():
    assert ledger.fee(99) == 99


def test_above_boundary():
    assert ledger.fee(101) == 303


def test_average_regression():
    ledger.ENTRIES.clear()
    ledger.post(10)
    ledger.post(30)
    assert ledger.average() == 20
