import rates
import ledger
import audit


def test_tier2_rate_updated():
    assert rates.TIER2_RATE == 3
    assert ledger.fee(150) == 450
    assert audit.fee_line(150) == "fee=450"


def test_tier1_regression():
    assert ledger.fee(50) == 50
    assert ledger.fee(99) == 99
