import rates
import ledger
import audit


def test_tier1_rate_updated():
    assert rates.TIER1_RATE == 2
    assert ledger.fee(50) == 100
    assert ledger.fee(150) == 450
    assert audit.fee_line(50) == "fee=100"


def test_full_chain():
    ledger.ENTRIES.clear()
    ledger.post(60)
    ledger.post(40)
    assert ledger.balance() == 100
    assert ledger.window_total(1) == 40
    assert ledger.average() == 50
    assert ledger.fee(100) == 200
