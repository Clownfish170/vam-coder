import hub


def test_quote():
    assert hub.interest(-2) == 0
    assert hub.interest(3) == 6
    assert hub.interest(0) == 0
