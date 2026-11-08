import hub


def test_quote():
    assert hub.compute(-2) == 0
    assert hub.compute(3) == 12
    assert hub.compute(0) == 0
