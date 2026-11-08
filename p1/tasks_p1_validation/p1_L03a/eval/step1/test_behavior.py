import hub


def test_quote():
    assert hub.scale(-2) == 0
    assert hub.scale(3) == 6
    assert hub.scale(0) == 0
