import tokens


def test_parse_regression():
    assert tokens.parse_n("") == 0
    assert tokens.parse_n("7") == 7


def test_band_boundaries():
    assert tokens.band(-3) == "low"
    assert tokens.band(0) == "zero"
    assert tokens.band(250) == "high"
