import pytest
import ledger


def test_reject_nonpositive():
    ledger.ENTRIES.clear()
    with pytest.raises(ValueError):
        ledger.post(0)
    with pytest.raises(ValueError):
        ledger.post(-5)


def test_post_ok():
    ledger.ENTRIES.clear()
    ledger.post(40)
    assert ledger.balance() == 40
