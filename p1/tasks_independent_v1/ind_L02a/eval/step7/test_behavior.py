import ledger


def test_average():
    ledger.ENTRIES.clear()
    ledger.post(10)
    ledger.post(30)
    assert ledger.average() == 20


def test_average_empty():
    ledger.ENTRIES.clear()
    assert ledger.average() == 0


def test_fee_regression():
    assert ledger.fee(150) == 450
