import hub


def test_quote():
    assert hub.fee_of(-2) == 0
    assert hub.fee_of(3) == 9
    assert hub.fee_of(0) == 0
