import ledger


def test_balance():
    ledger.ENTRIES.clear()
    ledger.post(50)
    ledger.post(30)
    assert ledger.balance() == 80


def test_balance_empty():
    ledger.ENTRIES.clear()
    assert ledger.balance() == 0


def test_post_regression():
    ledger.ENTRIES.clear()
    ledger.post(7)
    assert ledger.ENTRIES == [7]
