import hub


def test_quote():
    assert hub.cost(-2) == 0
    assert hub.cost(3) == 15
    assert hub.cost(0) == 0
