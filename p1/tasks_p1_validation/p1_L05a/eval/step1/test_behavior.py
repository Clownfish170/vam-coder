import hub


def test_quote():
    assert hub.points(-2) == 0
    assert hub.points(3) == 18
    assert hub.points(0) == 0
