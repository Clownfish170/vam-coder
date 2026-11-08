import audit
import ledger


def test_fee_line():
    assert audit.fee_line(50) == "fee=50"
    assert audit.fee_line(150) == "fee=300"


def test_line_regression():
    assert audit.line(9) == "amt=9"


def test_window_regression():
    ledger.ENTRIES.clear()
    ledger.post(1)
    ledger.post(2)
    assert ledger.window_total(1) == 2
