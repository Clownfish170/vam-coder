import hub


def test_quote():
    assert hub.quote(-2) == 0
    assert hub.quote(3) == 9
    assert hub.quote(0) == 0
