import shop


def test_quote_fast():
    assert shop.quote_fast(2) == 18


def test_quote():
    assert shop.quote(2) == 18
