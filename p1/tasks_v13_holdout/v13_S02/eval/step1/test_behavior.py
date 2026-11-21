import tokens


def test_blank_returns_zero():
    assert tokens.parse_n("") == 0
    assert tokens.parse_n("   ") == 0


def test_negative_returns_zero():
    assert tokens.parse_n("-5") == 0


def test_normal_int():
    assert tokens.parse_n("42") == 42
