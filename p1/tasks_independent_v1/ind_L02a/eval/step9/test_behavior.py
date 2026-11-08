import ledger


def test_window_zero():
    ledger.ENTRIES.clear()
    ledger.post(10)
    ledger.post(20)
    assert ledger.window_total(0) == 0


def test_window_negative():
    ledger.ENTRIES.clear()
    ledger.post(10)
    assert ledger.window_total(-3) == 0


def test_window_positive_regression():
    ledger.ENTRIES.clear()
    ledger.post(10)
    ledger.post(20)
    assert ledger.window_total(1) == 20
