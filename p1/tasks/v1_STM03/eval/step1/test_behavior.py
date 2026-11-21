import ratemap, shop


def test_quote():
    assert shop.quote(2) == 18


def test_apply_tier():
    assert ratemap.apply_tier(2, 'gold') == 18
