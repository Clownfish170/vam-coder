import ledger


def test_fee_tier1():
    assert ledger.fee(50) == 50


def test_fee_tier2():
    assert ledger.fee(150) == 300


def test_post_regression():
    import pytest
    ledger.ENTRIES.clear()
    with pytest.raises(ValueError):
        ledger.post(-1)
    ledger.post(10)
    assert ledger.balance() == 10
