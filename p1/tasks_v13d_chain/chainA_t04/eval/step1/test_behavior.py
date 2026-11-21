def test():
    from engine import quote
    assert quote(-1) == 0
    assert quote(5) == 50
