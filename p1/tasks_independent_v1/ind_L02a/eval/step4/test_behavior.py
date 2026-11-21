import ledger


def test_window():
    ledger.ENTRIES.clear()
    for x in (10, 20, 30, 40):
        ledger.post(x)
    assert ledger.window_total(2) == 70


def test_window_larger_than_size():
    ledger.ENTRIES.clear()
    ledger.post(5)
    ledger.post(6)
    assert ledger.window_total(10) == 11


def test_fee_regression():
    assert ledger.fee(50) == 50
    assert ledger.fee(150) == 300
