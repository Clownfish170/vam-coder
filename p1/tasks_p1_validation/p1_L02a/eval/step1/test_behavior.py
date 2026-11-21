import hub


def test_quote():
    assert hub.price(-2) == 0
    assert hub.price(3) == 12
    assert hub.price(0) == 0
